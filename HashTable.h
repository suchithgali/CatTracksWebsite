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
private:
    int buckets;
    ArrayList<T> keys;
    ArrayList<LinkedList<std::list<T>>*> data;

public:
    HashTable() : buckets(0), keys(), data() {}

    HashTable(ArrayList<T> bus_keys){
        this->buckets = bus_keys.getsize();
        for (int i = 0; i < buckets; i++){
            keys.append(bus_keys[i]);
            data.append(new LinkedList<std::list<T>>());
        }
    }

    int HashInts(int val){
        return val % buckets;
    }

    int HashStrings(std::string val){
        int sum = 0;
        for (int i = 0; i < val.length(); i++){
            sum += static_cast<int>(val[i]);
        }
        return sum % getBuckets();
    }

    LinkedList<std::list<T>>*& operator[](int index){
        return data[index];
    }

    int getBuckets(){
        return buckets;
    }

    void appendHashes(ArrayList<T> bus_keys, ArrayList<std::list<T>> values) {
        int limit = std::min({bus_keys.getsize(), values.getsize(), data.getsize()});
        for (int i = 0; i < limit; i++) {
            data[i]->appendinLL(values[i]);
        }
    }
    
    ~HashTable() {
        for (int i = static_cast<int>(data.getsize()) - 1; i >= 0; i--) {
            if (data[i] != nullptr) {
            delete data[i];
            data[i] = nullptr; // Avoid double deletion
        }
        }
    }

    friend std::ostream& operator<< <>(std::ostream& os, const HashTable<T>& table);
};

template <class T>
std::ostream& operator<<(std::ostream& os, const HashTable<T>& table){

    for (int i = 0; i < table.keys.getsize(); i++){
        os<< i << " " << table.keys[i] << ": " << *(table.data[i]) << std::endl;
    }
    
    return os;
}

#endif






