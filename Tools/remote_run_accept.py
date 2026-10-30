import sys, time
sys.path.insert(0, r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
from remote_execution import RemoteExecution, MODE_EXEC_FILE

re = RemoteExecution()
re.start()
nodes = []
for i in range(20):
    time.sleep(1.0)
    nodes = re.remote_nodes
    print("discover", i, nodes)
    if nodes:
        break
if not nodes:
    re.stop()
    raise SystemExit("NO_NODES")
print("using", nodes[0])
re.open_command_connection(nodes[0]["node_id"])
path = r"C:\Users\Administrator\Desktop\ai陀螺游戏\beyblade-unreal-prototype\Tools\accept_after_pie.py"
result = re.run_command(path, exec_mode=MODE_EXEC_FILE)
print("CMD_RESULT", result)
re.stop()