#ifndef HASH_TABLE
#define HASH_TABLE

#include "ArrayList.h"
#include "LinkedList.h"
#include <string>
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

    void appendInt(int val){
        int hashCode = 0;
        hashCode = HashInts(val);
        data[hashCode].appendinLL(val);
    }

    void appendString(std::string val_string){
        int hashCode = 0;
        hashCode = HashStrings(val_string);
        data[hashCode].appendinLL(val_string);
    }

    friend std::ostream& operator<< <>(std::ostream& os, const HashTable<T>& table);
};

template <class T>
std::ostream& operator<<(std::ostream& os, const HashTable<T>& table){
    // So we can cout the table

    for (int i = 0; i < table.buckets; i++){
        os<< i << ": " << table.data[i] << std::endl;
    }
    
    return os;
}

#endif






