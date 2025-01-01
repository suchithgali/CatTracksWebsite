#ifndef ARRAY_LIST
#define ARRAY_LIST

#include <iostream>
#include <ostream>


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


public:
    ArrayList(){
        capacity = 1;
        arr = new T[capacity];
        count = 0;
    }

    ArrayList(const ArrayList& other){
        capacity = other.capacity;
        arr = new T[capacity];
        count = other.count;
        for (int i = 0; i < count; i++){
            arr[i] = other.arr[i];
        }
    }

    void append(T value){
        arr[count] = value;
        count++;

        inflate();
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