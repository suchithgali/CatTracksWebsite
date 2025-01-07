#ifndef LINKED_LIST
#define LINKED_LIST

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
class LinkedList{
    Node<T>* front;
    Node<T>* back;
public:
    LinkedList(){
        front = nullptr;
        back = nullptr;
    }

    //method that adds a node to a linked list
    void append(T val){
        if (front == nullptr){
            front = new Node<T>(val);
        }
        else{
            Node* temp = front;
            while (temp->next != nullptr){
                temp = temp->next;
            }
            temp->next = new Node<T>(val);
            back = temp->next;
        }
    }
};







#endif 