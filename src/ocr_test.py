import easyocr
import cv2


IMAGE_PATH = "data/plates/test_plate.jpg"


def main():

    reader = easyocr.Reader(
        ["en"],
        gpu=False
    )

    image = cv2.imread(IMAGE_PATH)

    if image is None:
        print("❌ Plate image not found")
        return

    results = reader.readtext(image)

    if not results:
        print("❌ No text detected")
        return

    for detection in results:

        bbox, text, confidence = detection

        print("Text:", text)
        print("Confidence:", round(confidence, 3))


if __name__ == "__main__":
    main()