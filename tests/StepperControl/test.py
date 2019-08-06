from MotorController import MotorController


revs = int(input("Revolutions: "))
sleep = float(input("Milliseconds sleep: "))

controller = MotorController([7, 11, 13, 15], sleep, 512)
controller.init()

print("Starting")
for cycle in range(revs):
    controller.move_angle(360)
print("Done")

controller.cleanup()
