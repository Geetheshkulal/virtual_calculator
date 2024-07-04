from django.shortcuts import render
from django.http import StreamingHttpResponse
import cv2
from cvzone.HandTrackingModule import HandDetector

class Button:
    def __init__(self, pos, width, height, value):
        self.pos = pos
        self.width = width
        self.height = height
        self.value = value

    def draw(self, img):
        cv2.rectangle(img, self.pos, (self.pos[0] + self.width, self.pos[1] + self.height), (225, 225, 225), cv2.FILLED)
        cv2.rectangle(img, self.pos, (self.pos[0] + self.width, self.pos[1] + self.height), (50, 50, 50), 3)
        cv2.putText(img, self.value, (self.pos[0] + 40, self.pos[1] + 60), cv2.FONT_HERSHEY_PLAIN, 2, (50, 50, 50), 2)

    def checkClick(self, x, y, img):
        if self.pos[0] < x < self.pos[0] + self.width and self.pos[1] < y < self.pos[1] + self.height:
            cv2.rectangle(img, self.pos, (self.pos[0] + self.width, self.pos[1] + self.height), (255, 255, 255), cv2.FILLED)
            cv2.rectangle(img, self.pos, (self.pos[0] + self.width, self.pos[1] + self.height), (50, 50, 50), 3)
            cv2.putText(img, self.value, (self.pos[0] + 25, self.pos[1] + 80), cv2.FONT_HERSHEY_PLAIN, 5, (0, 0, 0), 5)
            return True
        else:
            return False

def home(request):
    return render(request, 'calculator_app/video_feed.html')

def generate_frames():
    cap = cv2.VideoCapture(0)
    cap.set(3, 1200)  # Width
    cap.set(4, 720)  # Height

    detector = HandDetector(detectionCon=0.8, maxHands=1)

    # Creating buttons
    buttonListValues = [['7', '8', '9', '*'],
                        ['4', '5', '6', '-'],
                        ['1', '2', '3', '+'],
                        ['0', '/', '.', '=']]
    buttonList = []
    for x in range(4):
        for y in range(4):
            xpos = x * 100 + 800  # Position of buttons
            ypos = y * 100 + 150
            buttonList.append(Button((xpos, ypos), 100, 100, buttonListValues[y][x]))

    myEquation = ''
    delayCounter = 0

    while True:
        success, img = cap.read()
        img = cv2.flip(img, 1)

        hands, img = detector.findHands(img, flipType=False)

        # Draw all buttons
        cv2.rectangle(img, (800, 40), (800 + 400, 70 + 100), (225, 225, 225), cv2.FILLED)
        cv2.rectangle(img, (800, 40), (800 + 400, 70 + 100), (50, 50, 50), 3)
        for button in buttonList:
            button.draw(img)

        if hands:
            lmList = hands[0]['lmList']
            x1, y1 = lmList[8][:2]
            x2, y2 = lmList[12][:2]
            length, _, img = detector.findDistance((x1, y1), (x2, y2), img)

            if length < 50:
                for i, button in enumerate(buttonList):
                    if button.checkClick(x1, y1, img) and delayCounter == 0:
                        myValue = buttonListValues[int(i % 4)][int(i / 4)]
                        if myValue == "=":
                            try:
                                myEquation = str(eval(myEquation))
                            except:
                                myEquation = "Error"
                        else:
                            myEquation += myValue
                        delayCounter = 1

        if delayCounter != 0:
            delayCounter += 1
            if delayCounter > 10:
                delayCounter = 0

        cv2.putText(img, myEquation, (810, 120), cv2.FONT_HERSHEY_PLAIN, 3, (50, 50, 50), 2)

        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def video_feed(request):
    return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')
