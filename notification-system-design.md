# Notification System Design Document

## STAGE 1: API DESIGN

### Selection: Server-Sent Events (SSE)

**Justification:**
We choose **SSE (Server-Sent Events)** over WebSocket and Polling.
- **WebSocket** is bi-directional, which is overkill since notifications are primarily server-to-client (uni-directional push). It also requires complex load balancing and state management.
- **Polling** introduces unnecessary network overhead and latency since the client repeatedly asks the server for updates even when there are none, draining battery and wasting resources.
- **SSE** provides a lightweight, uni-directional stream over standard HTTP. It natively supports auto-reconnection and works flawlessly with existing HTTP load balancers, making it ideal for scalable push notifications.

### API Endpoints
1. **GET /api/v1/notifications/stream**
   - **Description**: Subscribes the client to an SSE stream for real-time notifications.
   - **Headers**: `Authorization: Bearer <token>`, `Accept: text/event-stream`
   - **Response**: `text/event-stream` format (`data: {"id":"123","message":"Placement Update"}\n\n`)

2. **GET /api/v1/notifications**
   - **Description**: Fetch paginated historical notifications.
   - **Query Params**: `page`, `limit`, `status` (e.g. `unread`)
   - **Response schema**:
     ```json
     {
       "data": [
         {"id": "1", "type": "placement", "message": "...", "read": false, "timestamp": "..."}
       ],
       "meta": {"total": 500, "page": 1, "limit": 20}
     }
     ```

3. **PATCH /api/v1/notifications/{id}/read**
   - **Description**: Mark a specific notification as read.
   - **Request schema**: `{ "read": true }`
   - **Response**: `200 OK`

**Error Responses**:
- `401 Unauthorized`: Missing or invalid token.
- `400 Bad Request`: Invalid pagination parameters.
- `500 Internal Server Error`: Downstream failure.

---

## STAGE 2: DATABASE DESIGN

### Selection: NoSQL (MongoDB or DynamoDB)

**Why Chosen:**
Notifications are inherently write-heavy and append-only. They are also loosely structured (different notification types like `Event`, `Placement`, `Result` might require different metadata). A NoSQL database provides the horizontal scalability (sharding) needed to handle millions of rapid writes and flexible schemas.

### Schema Design
```json
{
  "_id": "uuid",
  "user_id": "uuid",
  "type": "string", // "placement", "result", "exam_alert"
  "content": "string",
  "metadata": "object", // Flexible structure depending on type
  "read": "boolean",
  "priority_score": "integer",
  "created_at": "timestamp",
  "expires_at": "timestamp" // TTL index for cleanup
}
```

### Growth & Partitioning Strategy
- **Partitioning (Sharding) Key**: `user_id`. Queries are almost always scoped to a specific user (e.g., "get unread notifications for user X"). Sharding by `user_id` ensures all notifications for a single user are located on the same physical node, preventing scatter-gather operations.
- **Growth Strategy**: Implement a **TTL (Time-To-Live)** index to automatically delete notifications older than 30 or 60 days, preventing infinite storage growth.

### Index Strategy
- `user_id` + `created_at` (Compound Index): For fetching a user's feed in chronological order.
- `user_id` + `read` + `created_at` (Compound Index): For quickly counting or fetching unread notifications.

---

## STAGE 3: QUERY OPTIMIZATION

### Scenario: 5 million rows

**Why Queries Become Slow:**
When a table reaches 5 million rows, an unindexed query forces the database to perform a **Full Table Scan**, reading every single row from disk into memory to find matches. This causes high CPU usage, slow I/O, and massive latency.

### "Index Everything" is Bad Advice
Creating an index for every column is detrimental because:
1. **Storage Cost**: Indexes take up physical disk space. Indexing everything doubles or triples the database size.
2. **Write Overhead**: Every `INSERT`, `UPDATE`, or `DELETE` requires updating the table *and* rebuilding the B-Tree for every single index. This severely degrades write performance.

### Composite Indexes & Covering Indexes
- **Composite Index**: An index on multiple columns (e.g., `(user_id, status, created_at)`). The order matters (most selective first).
- **Covering Index**: An index that contains all the columns needed for a query. If the database can satisfy the query reading *only* the index structure without hitting the actual table rows, performance increases drastically.

### Optimized SQL Query
Assuming we use SQL for this specific metric, an optimized query for unread placement notifications from the last 7 days:
```sql
-- Requires a composite index on (type, read_status, created_at)
SELECT id, content, created_at 
FROM notifications 
WHERE type = 'placement' 
  AND read_status = false 
  AND created_at >= NOW() - INTERVAL '7 days';
```

---

## STAGE 4: SCALABILITY DESIGN

### Analyzing "Fetch on Every Page Load"
**Problems:**
1. **Database Pressure**: Millions of users refreshing pages means millions of queries hitting the DB per second.
2. **Network Overhead**: Constantly transmitting the same unchanged data.
3. **Latency**: The user has to wait for a database round-trip before the UI renders.

### Improved Solution
1. **Push Updates (SSE)**: Use Server-Sent Events (Stage 1) to push the *unread count* or new notifications to the client only when they happen.
2. **Redis Caching**: Cache the "Unread Count" and the "Top 20 Recent Notifications" in Redis (`key: user:{id}:notifications`).
   - When a new notification is generated, push it to Redis (O(1)) and invalidate the old cache.
   - Page loads fetch directly from Redis memory in <1ms.
3. **Pagination**: Only load the first 20 notifications. Use cursor-based pagination for older data.
4. **Cache TTL**: Set a TTL of 24 hours on the Redis cache to evict inactive users from memory.

---

## STAGE 5: ARCHITECTURE REDESIGN

### Analyzing the Synchronous System
A system where `Service A` directly makes an HTTP call to the `Notification Service` is flawed:
- **Blocking**: `Service A` waits for the notification to send, slowing down its own response.
- **Failures & No Retries**: If the `Notification Service` is down, the notification is lost.
- **Scalability Issues**: A sudden burst of events (e.g., Exam Results released) will DDoS the Notification Service.

### Redesign: Event-Driven Architecture
We introduce a **Message Broker (e.g., Kafka or RabbitMQ)**.

1. **Producer**: `Service A` fires a "Placement Result" event into a Kafka Topic (`notifications_topic`) and immediately returns a response to the user. (Non-blocking).
2. **Message Queue**: Kafka buffers the messages. If there is a massive spike, Kafka safely stores them on disk.
3. **Consumer**: The `Notification Service` reads from the queue at its own pace (Consumer Pull).
4. **Retry & DLQ**: If sending a notification fails (e.g., email API down), the message is routed to a retry queue with exponential backoff. If it fails 5 times, it is sent to a **Dead-Letter Queue (DLQ)** for manual debugging.
5. **Idempotency**: The Consumer checks Redis or DB to see if `notification_id` was already processed, ensuring users don't get duplicate emails if the queue delivers the message twice.

### Sequence Flow
```text
[Placement Service] ---> (Publish Event) ---> [Kafka Topic]
                                                    |
                                            [Notification Consumer]
                                                    |---> Check Idempotency Key (Redis)
                                                    |---> Insert to NoSQL DB
                                                    |---> Push to SSE / Web Push
                                                    |---> (On Error) ---> [DLQ]
```

### Pseudocode
```python
def consume_notification_event(event):
    # 1. Idempotency Check
    if redis.exists(f"processed:{event.id}"):
        return  # Already processed
        
    try:
        # 2. Database Insert
        nosql_db.insert(event.to_document())
        
        # 3. Cache Update
        redis.lpush(f"user:{event.user_id}:feed", event)
        redis.incr(f"user:{event.user_id}:unread_count")
        
        # 4. Push to active SSE connections
        sse_manager.broadcast(event.user_id, event)
        
        # 5. Mark processed
        redis.setex(f"processed:{event.id}", ttl=86400, value="1")
        
    except Exception as e:
        # 6. Retry logic or DLQ routing
        route_to_retry_queue(event)
```

---

## STAGE 6: PRIORITY INBOX

### Approach and Efficient Maintenance
The priority inbox requires displaying the top $K$ (e.g., 10) most important unread notifications based on a combination of their `Priority` (Placement > Result > Event) and `Recency`. Sorting the entire dataset of $N$ notifications every time a new one arrives would take $O(N \log N)$ time, which is highly inefficient for a real-time system.

To solve this efficiently, we implemented a **Fixed-Size Min-Heap** (using Python's `heapq` module) wrapped inside a `PriorityInboxTracker` class. 

### Algorithm Complexity
- **Time Complexity**: Maintaining the top $K$ elements takes $O(\log K)$ time for each incoming notification. To process an initial batch of $N$ notifications, the complexity is $O(N \log K)$. This scales drastically better than $O(N \log N)$.
- **Space Complexity**: $O(K)$, as we only keep the top $K$ elements in memory.

### Handling New Real-time Notifications
Because the heap max size is strictly bounded to $K$:
1. When a new notification arrives via the real-time stream (SSE), we calculate its combined score.
2. If the heap currently has less than $K$ elements, we push it into the heap in $O(\log K)$ time.
3. If the heap is full, we compare its score to the minimum score currently in the heap (which sits at the root, accessible in $O(1)$ time).
4. If the new notification is more important than the minimum, we use a combined `heappushpop` operation to efficiently swap out the lowest priority notification and re-balance the heap in $O(\log K)$ time.
5. If it's less important, we simply discard it in $O(1)$ time.

This ensures the priority inbox always reflects the most important elements instantaneously with negligible CPU overhead.
