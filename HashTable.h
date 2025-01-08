#ifndef HASH_TABLE
#define HASH_TABLE

#include "LinkedList.h"
#include <string>

template <class T>
class HashTable{
    int buckets;
    ArrayList<LinkedList<T>> data;

    HashTable(){}

    int HashInts(int val){
        return val % buckets;
    }

    int HashStrings(std::string val){
        int sum = 0;
        for (int i = 0; i < val.length(); i++){
            sum += static_cast<int>(val[i]);
        }
        return sum;
    }

public:
    HashTable(int buckets){
        this->buckets = buckets;
        for (int i = 0; i < buckets; i++){
            data.append(LinkedList<T>());
        }
    }
};





#endif






