# Traffic Analyzer
Traffic Analyzer is a web application designed to analyze traffic using computer vision. The application offers several features to enhance traffic management and monitoring.

# Features
Wrong Lane Detection: Identify vehicles that are driving in the wrong lane.
Speed Detection: Measure the speed of vehicles in real-time.
Segmentation: Segment different parts of the video feed for detailed analysis.
Track using IP: Track vehicles using IP cameras (currently in development).

# How It Works
Upload Video: Users can upload their video feed to the application.
Dynamic ROI Drawing: Dynamically draw the Region of Interest (ROI) directly on the video.
Line Creation: Create lines on the video to perfectly match your video feed for accurate analysis.
These features allow for comprehensive traffic monitoring and management. The application can be a valuable tool for traffic management authorities, helping to improve road safety and efficiency.

# Future Enhancements
Accident Detection: Identify and alert about traffic accidents.
Fire Detection: Detect fires on the road.
Additional Features: Many other features for improved traffic management. 

# Usage
To use Traffic Analyzer, upload your video, draw the ROI, and create lines according to your video feed. Use the Track using IP feature to get feed and perform operations on them (in development).

Traffic Analyzer is a powerful tool for better traffic management, with many more features to come.



# Count The Vehicles:

![count](https://github.com/user-attachments/assets/d9e2b3bb-1838-4e64-8d9d-9b141f069a67)

![c](https://github.com/user-attachments/assets/db7c1a9f-418a-4eba-b3b9-0a9274ca311d)


Vehicle Counting
Traffic Analyzer offers a powerful vehicle counting feature, designed to provide accurate traffic data. This feature includes:

1) Dynamic Line Drawing: Users can draw lines in any direction on the video feed. This flexibility ensures that the counting lines can be perfectly aligned with the specific layout and traffic flow of the video.

2) Real-Time Counting: As vehicles cross the defined lines, the system automatically counts them. This data is displayed in real-time on the interface.

#How It Works
Upload Video: Users can upload their video feed to the application.
Draw Counting Lines: Users can draw multiple lines in any direction on the video feed, providing a customizable and precise setup for vehicle counting.
Real-Time Analysis: The system processes the video and counts the vehicles crossing each line, displaying the count in real-time.

By allowing users to draw lines dynamically and in any direction, Traffic Analyzer can adapt to various traffic scenarios and video feeds, making it a versatile tool for traffic analysis.



# Wrong Lane :  

![lane](https://github.com/user-attachments/assets/98d1db7f-dc01-4aa6-a3c9-f0a5fc3e3b8a)

![sp](https://github.com/user-attachments/assets/47704ec9-2ad8-490a-8e20-c6ce6178bc9f)



Wrong Lane Detection
Traffic Analyzer includes a robust Wrong Lane Detection feature, which helps in identifying vehicles driving in the wrong lane. This feature enhances road safety by allowing authorities to monitor and take action against lane violations.

#How It Works
1) Upload Video: Users can upload their video feed to the application.
2 ) Dynamic Line Drawing: Users can draw multiple lines in any direction on the video feed to define the lanes accurately.
Real-Time Detection: The system processes the video and identifies vehicles that cross the defined lanes incorrectly, indicating a wrong lane usage.

By allowing users to draw lines dynamically and in any direction, Traffic Analyzer ensures that lane definitions are accurate and adaptable to various road layouts and traffic conditions. This flexibility makes it a powerful tool for traffic enforcement and safety monitoring.

# Speed Detection : ![speed](https://github.com/user-attachments/assets/50c7c63b-7556-4762-bdaa-e8cbe0a89804)

![sr](https://github.com/user-attachments/assets/6bfd9cce-b161-47b1-be32-4cd50ba13131)

Traffic Analyzer incorporates an advanced Speed Detection feature, designed to measure the speed of vehicles accurately. This feature is optimized to work efficiently on both low-end and high-end GPUs, providing flexibility for various hardware configurations.

# How It Works
Upload Video: Users can upload their video feed to the application.
Speed Calculation: The system processes the video and calculates the speed of each detected vehicle.
Real-Time Analysis: For high-end GPUs, the system can process live video feeds and provide real-time speed data. For low-end GPUs, the system is optimized to process non-live videos efficiently without compromising accuracy.

Key Benefits
1) Optimized for Low-End GPUs: The speed detection algorithm is designed to work effectively on low-end GPUs, allowing users with limited hardware resources to still achieve accurate speed measurements.
2 ) Real-Time Processing: For users with high-end GPUs, the system can handle live video feeds and provide real-time speed data, making it suitable for various use cases.
Accurate Measurements: The algorithm ensures precise speed calculations, whether processing live feeds or non-live videos.
# Segmetationn
# Track using IP


![image](https://github.com/user-attachments/assets/129e359c-c92d-4ff4-9933-d062d162af94)

All of these processes can be performed using an IP and Port number, which you simply need to provide in the input field. However, for now, the cameras must be connected to the same WiFi network. In a future update, we plan to leverage cloud technology, where the video stream will first be sent to the cloud. From there, with the use of IP addresses and secure login protocols, we'll be able to process the video feeds over much longer distances, without the need for the cameras to be on the same local network.


![ip](https://github.com/user-attachments/assets/9025e782-216b-4a8e-bf60-1c061fa80655)

I am using the IP Webcam app on my phone to simulate a security camera and create a network that streams the video via an IP and Port. I then connect both the computer and the camera (phone) to the same network, input the IP and Port into the web app, and draw the line to detect and count cars. The setup works smoothly.



# All








