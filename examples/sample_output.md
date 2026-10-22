# How to reverse a linked list in Python

**Platform:** ChatGPT  
**Model:** `gpt-4o`  

---

### 🧑 User

How do I reverse a singly linked list in Python?

### 🤖 Assistant

Here's a simple iterative approach to reverse a singly linked list:

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def reverse_linked_list(head: ListNode) -> ListNode:
    prev = None
    current = head
    while current:
        next_node = current.next
        current.next = prev
        prev = current
        current = next_node
    return prev
```

**How it works:**
1. We maintain three pointers: `prev`, `current`, and `next_node`.
2. At each step, we reverse the `next` pointer of the current node.
3. Then advance all three pointers forward.
4. When `current` becomes `None`, `prev` is the new head.

Time complexity: O(n), Space complexity: O(1).

### 🧑 User

Can you also show a recursive version?

### 🤖 Assistant

Sure! Here's the recursive approach:

```python
def reverse_linked_list_recursive(head: ListNode) -> ListNode:
    if not head or not head.next:
        return head
    new_head = reverse_linked_list_recursive(head.next)
    head.next.next = head
    head.next = None
    return new_head
```

The recursive version uses the call stack to reach the end of the list, then reverses pointers on the way back. Time complexity is still O(n), but space complexity is O(n) due to the recursion stack.
