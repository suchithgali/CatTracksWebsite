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
Node<T>* sorted_BST(ArrayList<T>& list, int start, int end){
    if (start > end) {
        return nullptr;
    }
    int mid = (start + end) / 2;
    Node<T>* node = new Node<T>(list[mid]);
    node->left = sorted_BST(list, start, mid - 1);
    node->right = sorted_BST(list, mid + 1, end);
    return node;
}

// Prints the binary tree in a pretty way with branches
template <class T>
void print_tree(Node<T>* root, std::string indent = "", bool last = true) {
    if (!root) return;
    std::cout << indent;
    if (last) {
        std::cout << "└── ";
        indent += "    ";
    } else {
        std::cout << "├── ";
        indent += "│   ";
    }
    std::cout << root->data << std::endl;
    print_tree(root->left, indent, false);
    print_tree(root->right, indent, true);
}
template <class T>
void print_tree(Node<T>* root, std::string indent = "", bool last = true){
    if (!root) return;
}

#endif