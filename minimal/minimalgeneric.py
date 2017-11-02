def configparse():
    config = dict((line.split(": ") for line in open("minimalconfig.txt").read().split("\n") if line))
    config["webcam_resolution"] = tuple(map(int, config["webcam_resolution"].split("x")))
    config["message_port"], config["stream_port"] = (
        int(config["message_port"]), int(config["stream_port"])
    )
    return config
