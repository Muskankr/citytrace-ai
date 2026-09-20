from src.temporal_plate_consensus import plate_consensus


tests = [
    (
        "Track 95",
        [
            ("EY09VNS", 0.910),
            ("EY09VNS", 0.901),
            ("EY09VNS", 0.894),
            ("EY09VNS", 0.881),
            ("EY09VNS", 0.884),
            ("EY09VYS", 0.811),
            ("EYO3VVS", 0.649),
        ],
        "EY09VWS",
    ),

    (
        "Track 86",
        [
            ("EFIODZT", 0.933),
            ("EFIODZT", 0.933),
            ("EFIODZT", 0.921),
            ("EFIODZT", 0.940),
            ("EFIODZT", 0.934),
            ("EF1OOZT", 0.779),
            ("EFIODZI", 0.717),
        ],
        "EF10DZT",
    ),
]


for name, observations, expected in tests:

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    print("Observations:")

    for text, score in observations:
        print(f"  {text}  ({score:.3f})")

    result = plate_consensus(observations)

    print("\nConsensus :", result)
    print("Expected  :", expected)

    if result == expected:
        print("✅ CORRECT")
    else:
        print("⚠️ Needs additional contextual correction")