import os

exclusions = [""]

sources_to_format = []

for root, directory, files in os.walk(os.getcwd()):
    for source_file in files:
        if source_file.endswith(".py"):
            if source_file not in exclusions:
                print("Found file '%s'" % source_file)

                sources_to_format.append(os.path.join(root, source_file))
            else:
                print("Found excluded file '%s'" % source_file)

files_to_format = " ".join(sources_to_format)

os.system("black %s" % files_to_format)
