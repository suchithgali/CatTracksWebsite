#ifndef LINKED_LIST
#define LINKED_LIST

#include <list>
#include <ostream>
#include <iostream>

template <typename T>
std::ostream& operator<<(std::ostream& os, const std::list<T>& lst){
    os << "[";
    for(auto it = lst.begin(); it != lst.end(); ++it){
        os << *it;
        if(std::next(it) != lst.end()){
            os << ", ";
        }
    }
    os << "]";
    return os;
}


template <class T>
struct Node{
    T data;
    Node* next;
    Node* prev;

    Node(T data){
        this->data = data;
        next = nullptr;
        prev = nullptr;
    }
};

template <class T>
class LinkedList;

template <class T>
std::ostream& operator<<(std::ostream& os, const LinkedList<T>& container);

template <class T>
class LinkedList{
    Node<T>* front;
    Node<T>* back;
public:
    LinkedList(){
        front = nullptr;
        back = nullptr;
    }

    //method that adds a node to a linked list
    void appendinLL(T val){
        if (front == nullptr){
            front = new Node<T>(val);
            back = front;
        }
        else{
            Node<T>* temp = front;
            while (temp->next != nullptr){
                temp = temp->next;
            }
            temp->next = new Node<T>(val);
            temp->next->prev = temp;
            back = temp->next;
        }
    }

    ~LinkedList(){
        Node<T>* current = front;
        while(current){
            Node<T>* toDelete = current;
            current = current->next;
            delete toDelete;
        }
    }

    friend std::ostream& operator<< <>(std::ostream& os, const LinkedList<T>& list);
};


template <class T>
std::ostream& operator<<(std::ostream& os, const LinkedList<T>& list){
        Node<T>* current = list.front;
        while(current != nullptr){
            os << current->data;
            if(current->next != nullptr){
                os << " -> ";
            }
            current = current->next;
        }
        return os;
    }
    
#endif 