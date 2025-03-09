#ifndef ARRAY_LIST
#define ARRAY_LIST

#include <initializer_list>
#include "LinkedList.h"
#include <iostream>
#include <ostream>
#include <cmath>
#include <string>


template <class T>
class ArrayList;

template <class T>
std::ostream& operator<<(std::ostream& os, const ArrayList<T>& container);

template <class T>
class ArrayList{
protected:
    T* arr;
    int count;
    int capacity;

    void inflate(){
        if (count == capacity){
            int oldCapacity = capacity;
            capacity *= 2;

            T* temp = new T[capacity];

            for (int i = 0; i < oldCapacity; i++){
                temp[i] = arr[i];
            }

            T* old = arr;

            arr = temp;

            delete[] old;
        }
    }

    void deflate(){
        if (capacity > count * 2){
            capacity /= 2;
            T* temp = new T[capacity];

            for (int i = 0; i < count; i++){
                temp[i] = arr[i];
            }
            T* old = arr;
            arr = temp;
            delete [] old;
        }
    }


public:
    ArrayList(){
        capacity = 1;
        arr = new T[capacity];
        count = 0;
    }

    auto begin() {return arr;}
    auto end() {return arr + count;}

    ArrayList(const ArrayList& other){
        capacity = other.capacity;
        arr = new T[capacity];
        count = other.count;
        for (int i = 0; i < count; i++){
            arr[i] = other.arr[i];
        }
    }

   ArrayList& operator=(const ArrayList& other){
        if (this == &other){
            return *this;
        }
        delete[] arr;
        capacity = other.capacity;
        arr = new T[capacity];
        count = other.count;
        for (int i = 0; i < count; i++){
            arr[i] = other.arr[i];
        }
        return *this;
    }
    

    ArrayList(std::initializer_list<T> list) {
        count = list.size();
        capacity = (count == 0) ? 1 : (int)pow(2, ceil(std::log2(count)));

        arr = new T[capacity];
        
        int i = 0;
        for (auto it = list.begin(); it != list.end(); i++, it++) {
            arr[i] = *it;
        }
    }

   ArrayList insertionSort(ArrayList<T>& list){
    for (int i = 1; i < list.getsize(); i++){
       std::string temp = list[i];
        int j = i - 1;

        while (j >= 0 && list[j] > temp){
        list[j + 1] = list[j];
        j--;
        }
        list[j + 1] = temp;
    }
    return list;
    }

    void append(T value){
        if (count == capacity){
            inflate();
        }
        arr[count] = value;
        count++;
        
    }

     void append(LinkedList<std::list<T>>* value){
        if (count == capacity){
            inflate();
        }
        arr[count] = value;
        count++;
    }

    int getsize() const{
        return count;
    }

    T* getarr(){
        return arr;
    }

    void prepend(T val){
        if (count == capacity){
            inflate();
        }
        for (int i = count - 1; i >= 0; i--){
            arr[i + 1] = arr[i];
        }
        arr[0] = val;
        count++;
    }

    void removeFirst(){
        T* temp = new T[capacity];
        for (int i = 1; i < count; i++){
            temp[i - 1] = arr[i];
        }
        T* old = arr;
        arr = temp;
        delete [] old;
        count--;
    }

    void removeLast(){
        count--;
    }

    T& operator[](int index){
        return arr[index];
    }

    const T& operator[](int index) const {
        return arr[index];
    }

    int size() {
        return count;
    }
    
   int index(T target){
        int low = 0;
        int high = count - 1;

        while (low <= high){
            int middle = (low + high) / 2;
            T value = arr[middle];
            if (value < target){
                low = middle + 1;
            }
            else if (value > target){
                high = middle - 1;
            }
            else{
                return middle;
            }
        }
        return -1;
    } 

    std::string search(std::string target){
        int low = 0;
        int high = count - 1;

        while (low <= high){
            int middle = (low + high) / 2;
            std::string value = arr[middle];
            if (value < target){
                low = middle + 1;
            }
            else if (value > target){
                high = middle - 1;
            }
            else{
                return arr[middle];
            }
        }
        return "";
    }

    ~ArrayList(){
        delete[] arr;
    }

    friend std::ostream& operator<< <>(std::ostream& os, const ArrayList<T>& container);
    friend struct TestArrayList;
};

template <class T>
std::ostream& operator<<(std::ostream& os, const ArrayList<T>& container){
    for (int i = 0; i < container.count; i++){
        os << container.arr[i];
        if (i < container.count-1){
            os << ", ";
        }
    }
    return os;
}

#endif