#ifndef HASH_TABLE
#define HASH_TABLE

#include "ArrayList.h"
#include "LinkedList.h"
#include <string>
#include <list>
#include <ostream>
#include <typeinfo>

template <class T>
class HashTable;

template <class T>
std::ostream& operator<<(std::ostream& os, const HashTable<T>& container);

template <class T>
class HashTable{
    int buckets;
    ArrayList<LinkedList<T>> data;

    HashTable(){}

public:
    HashTable(int buckets){
        this->buckets = buckets;
        for (int i = 0; i < buckets; i++){
            data.append(LinkedList<T>());
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
        return sum % buckets;
    }

    int getBuckets(){
        return buckets;
    }

    void appendHash(std::string key, std::list<std::string> values){
        int index = HashStrings(key);
        for (const auto& v : values){
            data[index].appendinLL(v);
        }
    }

    friend std::ostream& operator<< <>(std::ostream& os, const HashTable<T>& table);
};

template <class T>
std::ostream& operator<<(std::ostream& os, const HashTable<T>& table){

    for (int i = 0; i < table.buckets; i++){
        os<< i << ": " << table.data[i] << std::endl;
    }
    
    return os;
}

#endif






