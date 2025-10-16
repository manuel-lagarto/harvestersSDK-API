from harvesters.core import Harvester

h = Harvester()

cti_path = "C:/Program Files/Balluff/ImpactAcquire/bin/x64/mvGenTLProducer.cti"
h.add_file(cti_path)
print(h.files)

h.update()
print(h.device_info_list)