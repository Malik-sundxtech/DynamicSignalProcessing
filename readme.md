# Maliks Project

## Table of Contents
[Overview](#overview) \
[PySide6](#pyside6) \
[Docker](#docker) \
[Pybind11 & CMake](#pybind-11--cmake) \
[Further development](#future-projectsskills-i-plan-on-working-with)





# Overview
PySide6
- Make an interactable GUI

Pybind11 & CMake
- Integrating C++ and Python together

Docker Desktop
- Being able to run code on every OS

GitHub Desktop
- Sharing code more seemleasly \
[GitHub troubleshooting guide](https://ohshitgit.com/)

Purpose of this project
1. UI with filter tick system (Can choose in what order to apply filters and adjust windowssize. hz range etc. from the 
UI also being able to switch between different images, choose to save etc.)
2. Calculate P values, clickable statistics (boxplot, barplot)
3. [PEP8 - Good code practice](https://peps.python.org/pep-0008/)


# PySide6
The GUI for this program is made using [PySide6](https://www.pythonguis.com/pyside6-tutorial/)

## Pybind 11 & CMAKE
To integrate C++ in Python we can use [pybind11](https://pybind11.readthedocs.io/en/stable/index.html)

Pybind11 makes it possible to use C++ in Python, but also to use Python in C++, this makes it possible to do [embedded programming with Python](https://pybind11.readthedocs.io/en/stable/advanced/embedding.html)!

.venv can interfer with cmake function and therefore it is important to `deactivate` the venv.


    mkdir build
    cd build
    cmake ..
    cmake --build . --config Release

Notes: 
Micocontrollers can't normally use languages like Python, and therefore need some extensions to make use of this. \
On the other hand RaspberryPi works like a small Linux OS and therefore can run any language a normal pc can.

## Docker
Newest knowledge: \
Apparently Docker doesn't work well with UI's and crashes. I need to figure out what it can be used for, if not UI's don't work with it.

[Docker guide](https://www.youtube.com/watch?v=DQdB7wFEygo ) \
Why is Docker good? \
It creates an image (operating system like) where all code runs the same - no more "It works on my pc" problems. \
This Docker runs Linux (Specifically Debian Linux). The OS can be changed in the Dockerfile

You need:
- Docker extension for vs code
- Docker desktop 
- Docker compose (helps your docker containers work together)

### Short explanation
To build all docker file you can run:
```bash
    docker init
```

Activate docker compose
```bash
docker compose up
```



### In depth explanation
Important to know:
Docker image and containers
Docker volumes are like folders where the docker can share files with its own containers

### To build the docker image write the following in the terminal:
```bash
docker build -t name .  
```
t stands for tag (name your file)

### To run the docker image write the following in the terminal:
```bash
docker run -p 9000:9000 name
```
-p 9000:9000 stands for port forwarding port 9000 (port on pc) to 9000 (port in docker container) 

### To activate docker compose type
```bash
docker compose up
```
Activate docker compose

```bash
docker compose down
```
Deactivate docker compose

When making docker containers seperate backend, frontend and database instead of lumping them in one.
This creates a multi container application 


Tutorial: 

Backend explanation:

Frontend explanation:

Database explanation:

 For further development:
 Docker build cloud builds containers 39 times faster, but is more complex to use. So good for big projects


 ## Future projects/skills I plan on working with:
ROS2 \
Foxglove \
Heartrate monitor (HRV calculation) \
Machine learning (PyTorch, KNN & KMeans) \
Electron \
API \
Numba 