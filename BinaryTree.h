#ifndef BINARY_TREE
#define BINARY_TREE

#include <iostream>
#include <ostream>
#include "ArrayList.h"

template <class T>
struct Node{
    T data;
    Node* left;
    Node* right;


    Node(T val){
        data = val;
    }
};

//creates a Binary Search Tree using a sorted ArrayList
template <class T>
Node<T>* sorted_BST(ArrayList<T> list, int start, int end){
    if (start > end) {
        return nullptr;
    }
    int mid = (start + end) / 2;
    Node<T>* node = new Node<T>(list[mid]);
    node->left = sorted_BST(list, start, mid - 1);
    node->right = sorted_BST(list, mid + 1, end);
    return node;
}

//traverses the sorted Binary Tree in order
template <class T>
void in_order_traversal(Node<T>* root){
    if (root == nullptr) {
        return;
    }
    in_order_traversal(root->left);
    std::cout << root->data << " ";
    in_order_traversal(root->right);
}

#endif