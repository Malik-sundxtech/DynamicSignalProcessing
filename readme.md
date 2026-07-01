In this project I have been working with


Implementation comments:
1. UI with filter tick system (Can choose in what order to apply filters and adjust windowssize. hz range etc. from the 
UI also being able to switch between different images, choose to save etc.)
2. Calculate P values, clickable statistics (boxplot, barplot)
3. [PEP8 - Good code practice](https://peps.python.org/pep-0008/)


# Applications
CMake 
- Integrating C++ and Python together

Docker Desktop
- Being able to run code on every OS

GitHub Desktop
- Sharing code more seemleasly 

# Coding skills
GUI
Real time signal processing 

# Future projects/skills I plan on working with:
ROS2 
Foxglove
Heartrate monitor (HRV calculation)
Machine learning (PyTorch, KNN & KMeans)
Electron
API

CMAKE:
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

Docker:
Why is Docker good? \
It creates an image (operating system like) where all code runs the same - no more "It works on my pc" problems

You need:
- Docker extension for vs code
- Docker desktop 
- Docker compose (helps your docker containers work together)

Important to know:
Docker image and containers
Docker volumes are like folders where the docker can share files with its own containers

# To build the docker image write the following in the terminal:
```bash
docker build -t name .  
```
t stands for tag (name your file)

# To run the docker image write the following in the terminal:
```bash
docker run -p 9000:9000 name
```
-p 9000:9000 stands for port forwarding port 9000 (port on pc) to 9000 (port in docker container) 

# To activate docker compuse type
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


Tutorial: https://www.youtube.com/watch?v=DQdB7wFEygo 

Backend explanation:

Frontend explanation:

Database explanation:
 
To build all docker file you can run:
```bash
    docker init
```

 For further development:
 Docker build cloud builds containers 39 times faster, but is more complex to use. So good for big projects