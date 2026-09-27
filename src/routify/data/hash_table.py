"""chained hash table for o(1) average location lookup (member 5)."""

class _Node:
    #basic node for handling collisions via linked list.
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None

class HashTable:
    #initializes the hash table with a default capacity.
    def __init__(self, capacity: int = 64) -> None:
        self.capacity = capacity
        self.size = 0
        self.table: list[_Node | None] = [None] * self.capacity

    #computes the index for a given key using polynomial rolling hash.
    def _hash(self, key) -> int:
        hash_val = 0
        for char in str(key):
            hash_val = (hash_val * 31 + ord(char)) & 0xFFFFFFFF
        return hash_val % self.capacity

    #inserts a key-value pair or updates it if the key already exists.
    def insert(self, key, value) -> None:
        index = self._hash(key)
        current = self.table[index]
        
        while current:
            if current.key == key:
                current.value = value
                return
            current = current.next
            
        new_node = _Node(key, value)
        new_node.next = self.table[index]
        self.table[index] = new_node
        self.size += 1
        
        if self.size / self.capacity > 0.75:
            self._resize()

    #looks up a key and returns its value or throws an error.
    def search(self, key):
        current = self.table[self._hash(key)]
        
        while current:
            if current.key == key:
                return current.value
            current = current.next
            
        raise KeyError(key)

    #finds and removes a key-value pair from the table.
    def remove(self, key) -> None:
        index = self._hash(key)
        previous = None
        current = self.table[index]
        
        while current:
            if current.key == key:
                if previous:
                    previous.next = current.next
                else:
                    self.table[index] = current.next
                self.size -= 1
                return
            previous, current = current, current.next
            
        raise KeyError(key)

    #doubles the capacity and rehashes everything to maintain fast lookups.
    def _resize(self) -> None:
        old_table = self.table
        self.capacity *= 2
        self.table = [None] * self.capacity
        self.size = 0
        
        for bucket in old_table:
            current = bucket
            while current:
                self.insert(current.key, current.value)
                current = current.next

    #returns the total number of elements currently in the table.
    def __len__(self) -> int:
        return self.size

    #allows bracket access like table[key] to fetch a value.
    def __getitem__(self, key):
        return self.search(key)

    #allows bracket assignment like table[key] = value.
    def __setitem__(self, key, value) -> None:
        self.insert(key, value)

    #allows using the 'in' keyword to check if a key exists.
    def __contains__(self, key) -> bool:
        try:
            self.search(key)
            return True
        except KeyError:
            return False

    #fetches a value safely without throwing an error if it's missing.
    def get(self, key, default=None):
        try:
            return self.search(key)
        except KeyError:
            return default

    #generates all key-value pairs stored in the table.
    def items(self):
        for bucket in self.table:
            current = bucket
            while current:
                yield current.key, current.value
                current = current.next

    #generates all the keys stored in the table.
    def keys(self):
        for bucket in self.table:
            current = bucket
            while current:
                yield current.key
                current = current.next

    #makes the hash table itself iterable by yielding keys.
    def __iter__(self):
        return self.keys()

    #generates all the values stored in the table.
    def values(self):
        for bucket in self.table:
            current = bucket
            while current:
                yield current.value
                current = current.next
