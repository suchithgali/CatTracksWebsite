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
    ArrayList<std::string> keys;
    // Store LinkedList objects directly instead of pointers
    ArrayList<LinkedList<std::list<T>>> data;
    ArrayList<LinkedList<HashTable<T>>> dataTables;
    ArrayList<LinkedList<T>> dataT;

public:
    // Default Constructor
    HashTable() 
        : buckets(1), keys(), data(), dataTables(), dataT() {}

    // Constructor with bucket size
    HashTable(int buckets){
        this->buckets = buckets;
        for (int i = 0; i < buckets; i++){
            dataT.append(LinkedList<T>());
            data.append(LinkedList<std::list<T>>());
            dataTables.append(LinkedList<HashTable<T>>());
        }
    }

    // Constructor with bus_keys
    HashTable(ArrayList<T>& bus_keys){
        this->buckets = bus_keys.getsize();
        for (int i = 0; i < buckets; i++){
            keys.append(bus_keys[i]);
            data.append(LinkedList<std::list<T>>());
            dataTables.append(LinkedList<HashTable<T>>());
            dataT.append(LinkedList<T>());
        }
    }

    // Copy Constructor (Default is sufficient)
    HashTable(const HashTable<T>& other) = default;

    // Move Constructor (Default is sufficient)
    HashTable(HashTable<T>&& other) noexcept = default;

    // Copy Assignment Operator (Default is sufficient)
    HashTable<T>& operator=(const HashTable<T>& other) = default;

    // Move Assignment Operator (Default is sufficient)
    HashTable<T>& operator=(HashTable<T>&& other) noexcept = default;

    // Destructor (Default is sufficient)
    ~HashTable() = default;

    // Iterator Support
    auto begin() { return keys[0]; }
    auto end() { return keys.end(); }

    // Hash Functions
    int HashInts(int val){
        return val % buckets;
    }

    int HashStrings(const std::string& val) const {
        if(data.getsize() == 0){
            throw std::runtime_error("HashTable is empty");
        }
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

    // Accessors
    ArrayList<std::string> getKeys() const{
        return keys;
    }

    ArrayList<LinkedList<std::list<T>>> getValues(){
        return data;
    }

    LinkedList<HashTable<T>> getValues(std::string busname){
        int index = HashStrings(busname);
        return dataTables[index];
    }

    // Search Functions
    std::string search(std::string val){
        int index = keys.index(val);
        if (index >= 0){
             return keys[index];
        }
        else{
            return "";
        }
    }

    int searchforKeyIndex(float val){
        int index = 0;
        if(data.getsize() == 0){
            throw std::runtime_error("HashTable is empty");
        }
        bool first = true;
        for (int i = 0; i < data.getsize(); i++){
            LinkedList<std::list<T>> bucket = data[i];
            for(auto it = bucket.begin(); it != bucket.end(); ++it){
                for(const T& item : *it){
                    if(first || item == val){
                        index = i;
                        first = false;
                    }
                }
            }
        }
        return index;
    }

    std::string searchforKey(float val){
        int index = 0;
        if(data.getsize() == 0){
            throw std::runtime_error("HashTable is empty");
        }
        bool first = true;
        for (int i = 0; i < data.getsize(); i++){
            LinkedList<std::list<T>> bucket = data[i];
            for(auto it = bucket.begin(); it != bucket.end(); ++it){
                for(const T& item : *it){
                    if(first || item == val){
                        index = i;
                        first = false;
                    }
                }
            }
        }
        if(index >= keys.getsize()){
            throw std::out_of_range("Index out of range in searchforKey");
        }
        return keys[index];
    }

    // Overloaded Operators
    std::string operator[](int key){
        int index = HashInts(key);
        if(index < 0 || index >= keys.getsize()){
            throw std::out_of_range("Key index out of range");
        }
        return keys[index];
    }

    std::string operator[](std::string key){
        int index = HashStrings(key);
        if(index < 0 || index >= keys.getsize()){
            throw std::out_of_range("Key index out of range");
        }
        return keys[index];
    }

    // Additional Methods
    int getBuckets() const{
        return buckets;
    }

    float getMinValue(){
        if(data.getsize() == 0){
            throw std::runtime_error("HashTable is empty");
        }
        float min;
        bool first = true;
        for(int i = 0; i < data.getsize(); i++){
            LinkedList<std::list<T>> bucket = data[i];
            for(auto it = bucket.begin(); it != bucket.end(); ++it){
                for(const T& item : *it){
                    if(first || item < min){
                        min = item;
                        first = false;
                    }
                }
            }
        }
        return min;
    }

    // Append Methods
    void appendTable(int hashCode, std::string& value, HashTable<T>& values){
        if(data.getsize() == 0){
            throw std::runtime_error("HashTable is empty");
        }
        keys[hashCode] = value;
        dataTables[hashCode].appendinLL(values);
    }

    void appendHashes(ArrayList<T>& bus_keys, ArrayList<std::list<T>>& values) {
        if(data.getsize() == 0){
            throw std::runtime_error("HashTable is empty");
        }
        for (int i = 0; i < buckets; i++) {
            int hash = HashStrings(bus_keys[i]);
            data[hash].appendinLL(values[i]);
        }
    }

    void appendHashes(ArrayList<T>& bus_keys, ArrayList<HashTable<T>>& values) {
        if(data.getsize() == 0){
            throw std::runtime_error("HashTable is empty");
        }
        for (int i = 0; i < buckets; i++) {
            int hash = HashStrings(bus_keys[i]);
            dataTables[hash].appendinLL(values[i]);
        }
    }

    void appendHashes(ArrayList<T>& bus_keys, HashTable<T>& values) {
        if(data.getsize() == 0){
            throw std::runtime_error("HashTable is empty");
        }
        for (int i = 0; i < buckets; i++) {
            int hash = HashStrings(bus_keys[i]);
            dataTables[hash].appendinLL(values);
        }
    }

    void appendHashes(ArrayList<std::string>& bus_keys, T distances) {
        if(data.getsize() == 0){
            throw std::runtime_error("HashTable is empty");
        }
        for (int i = 0; i < buckets; i++) {
            keys.append(bus_keys[i]);
            int hash = HashStrings(bus_keys[i]);
            dataT[hash].appendinLL(distances);
        }
    }

    void appendHashes(std::string bus_keys, std::string busnames) {
        if(data.getsize() == 0){
            throw std::runtime_error("HashTable is empty");
        }
        int hash = HashStrings(bus_keys);
        dataT[hash].appendinLL(busnames);
    }

    // Friend Declaration for Operator<<
    friend std::ostream& operator<< <>(std::ostream& os, const HashTable<T>& table);
};

// Friend function implementation
template <class T>
std::ostream& operator<<(std::ostream& os, const HashTable<T>& table){
    for (int i = 0; i < table.keys.getsize(); i++){
        int j = table.HashStrings(table.keys[i]);
        os << table.keys[i] << ": " << table.data[j] << std::endl;
        os << std::endl;
    }
    return os;
}

#endif