#ifndef HASH_TABLE
#define HASH_TABLE

#include "ArrayList.h"
#include "LinkedList.h"
#include <string>
#include <list>
#include <ostream>
#include <typeinfo>
#include <algorithm>

template <class T>
class HashTable;

template <class T>
std::ostream& operator<<(std::ostream& os, const HashTable<T>& container);

template <class T>
class HashTable{
protected:
    int buckets;
    ArrayList<T> keys;
    ArrayList<LinkedList<std::list<T>>*> data;

public:
    HashTable() : buckets(0), keys(), data() {}

    HashTable(int buckets){
        this->buckets = bus_keys.getsize();
    }

    HashTable(ArrayList<T> bus_keys){
        this->buckets = bus_keys.getsize();
        for (int i = 0; i < buckets; i++){
            keys.append(bus_keys[i]);
            data.append(new LinkedList<std::list<T>>());
        }
    }

    auto begin() {return keys[0];}
    auto end() {return keys[getBuckets - 1];}

    int HashInts(int val){
        return val % buckets;
    }

    int HashStrings(const std::string& val) const {
        int hashValue = 0;
        int prime = 41;
        int mod = 1000000009;
        int power = 1;
        for (char c : val){
            char lower = std::tolower(c);
            if (lower < 'a' || lower > 'z'){
                continue;
            }
            hashValue = (hashValue + (c - 'a' + 1) * power) % mod;
            power = (power * prime) % mod;
        }

        return (hashValue % buckets + buckets) % buckets;
    }

    ArrayList<T> getKeys(){
        return keys;
    }

    std::string search(std::string val){
        int index = keys.index(val)
        return keys[index];
    }

    HashTable& operator[](std::string key){
        int index = HashStrings(key);
        return data[index];
    }

    int getBuckets(){
        return buckets;
    }

    void appendTable(int hashCode, std::string value, HashTable<T> table){
        table.keys[hashCode] = value;
        table.data[hashCode]->appendinLL(table);
    }

    void appendHashes(ArrayList<T> bus_keys, ArrayList<std::list<T>> values) {
        for (int i = 0; i < buckets; i++) {
            int hash = HashStrings(bus_keys[i]);
            data[hash]->appendinLL(values[i]);
        }
    }

    void appendHashes(ArrayList<T> bus_keys, ArrayList<HashTable<T>> values) {
        for (int i = 0; i < buckets; i++) {
            int hash = HashStrings(bus_keys[i]);
            data[hash]->appendinLL(values[i]);
        }
    }

    
    ~HashTable() {
        for (int i = static_cast<int>(data.getsize()) - 1; i >= 0; i--) {
            delete data[i];
        }
    }


    friend std::ostream& operator<< <>(std::ostream& os, const HashTable<T>& table);
};

template <class T>
std::ostream& operator<<(std::ostream& os, const HashTable<T>& table){
    for (int i = 0; i < table.keys.getsize(); i++){
        int j = table.HashStrings(table.keys[i]);
        os<< table.keys[i] << ": " << *(table.data[j]) << std::endl;
        os << std::endl;
    }
    
    return os;
}

#endif