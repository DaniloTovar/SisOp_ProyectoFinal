import os
import sys, getopt
import signal
import time
from gpiozero import LED
from edge_impulse_linux.audio import AudioImpulseRunner

# Set up GPIO using gpiozero
led = LED(18)
led_status = False  # False = off, True = on

runner = None

def signal_handler(sig, frame):
    print('Interrupted')
    if runner:
        runner.stop()
    led.off()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def help():
    print('Usage: python classify.py <path_to_model.eim> <audio_device_ID, optional>')

def main(argv):
    global led_status

    try:
        opts, args = getopt.getopt(argv, "h", ["--help"])
    except getopt.GetoptError:
        help()
        sys.exit(2)

    for opt, _ in opts:
        if opt in ('-h', '--help'):
            help()
            sys.exit()

    if len(args) == 0:
        help()
        sys.exit(2)

    model = args[0]
    dir_path = os.path.dirname(os.path.realpath(__file__))
    modelfile = os.path.join(dir_path, model)

    with AudioImpulseRunner(modelfile) as runner:
        try:
            model_info = runner.init()
            labels = model_info['model_parameters']['labels']
            print(f'Loaded runner for "{model_info["project"]["owner"]} / {model_info["project"]["name"]}"')

            selected_device_id = None
            if len(args) >= 2:
                selected_device_id = int(args[1])
                print(f"Device ID {selected_device_id} has been provided as an argument.")

            for res, audio in runner.classifier(device_id=selected_device_id):
                print(f'Result ({res["timing"]["dsp"] + res["timing"]["classification"]} ms.)', end=' ')

                scores = res['result']['classification']
                # for label in labels:
                #     score = scores[label]
                #     print(f'{label}: {score:.2f}', end='\t')
                # print('', flush=True)

                # LED control logic using gpiozero
                if scores.get('encender', 0) > 0.8:
                    if not led_status:
                        led.on()
                        led_status = True
                        print("LED turned ON")
                elif scores.get('Apagar', 0) > 0.8:
                    if led_status:
                        led.off()
                        led_status = False
                        print("LED turned OFF")

        finally:
            if runner:
                runner.stop()
            led.off()

if __name__ == '__main__':
    main(sys.argv[1:])
