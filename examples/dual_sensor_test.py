import platform
import sys
import os
import pickle

from harvesters.core import Harvester, ImageAcquirer

# Change CTI_PATH as needed for the target GenTL producer
if platform.system() == "Windows":
    CTI_PATH = r"C:/Program Files/Balluff/ImpactAcquire/bin/x64/mvGenTLProducer.cti"
elif platform.system() == "Linux":
    CTI_PATH = r"/opt/cvb-14.01.008/drivers/genicam/libGevTL.cti"
else:
    raise OSError("Operating system not supported!")

h = Harvester()

h.add_file(CTI_PATH)

h.update()
print(f"Total found devices: {len(h.device_info_list)}")

devices_list = []
for idx, device_info in enumerate(h.device_info_list):
    devices_list.append({
        'index': idx,
        'id': device_info.id_,
        'vendor': device_info.vendor,
        'model': device_info.model,
        'serial_number': device_info.serial_number,
        'user_defined_name': device_info.user_defined_name
    })
    print(f"Found device {idx}: Name = {device_info.user_defined_name}; Model = {device_info.model}; S/N = {device_info.serial_number}")

ia_m = h.create({'user_defined_name': '21815765M'})
ia_s = h.create({'user_defined_name': '21815765S'})

ia_m.start()
ia_s.start()

with ia_m.fetch() as buffer_m: # type: ignore
    print(f"Master buffer: {buffer_m}")    
    comps_out_m = []
    for comp_m in buffer_m.payload.components: # type: ignore
        comps_out_m.append({
            "width": comp_m.width, # type: ignore
            "height": comp_m.height, # type: ignore
            "data": comp_m.data.copy(), # type: ignore
            "dtype": comp_m.data.dtype, # type: ignore
            "data_format": comp_m.data_format,
            "component_type": type(comp_m).__name__,
        })

with ia_s.fetch() as buffer_s: # type: ignore
    print(f"Slave buffer: {buffer_s}")
    comps_out_s = []
    for comp_s in buffer_s.payload.components: # type: ignore
        comps_out_s.append({
            "width": comp_s.width, # type: ignore
            "height": comp_s.height, # type: ignore
            "data": comp_s.data.copy(), # type: ignore
            "dtype": comp_s.data.dtype, # type: ignore
            "data_format": comp_s.data_format,
            "component_type": type(comp_s).__name__,
        })        


with open("./_frame_dumps/frame_dump_dual_master_scan6.pkl", "wb") as f:
    pickle.dump(comps_out_m, f)
    
with open("./_frame_dumps/frame_dump_dual_slave_scan6.pkl", "wb") as f:
    pickle.dump(comps_out_s, f)
    
ia_m.stop()
ia_s.stop()

ia_m.destroy()
ia_s.destroy()

h.reset()