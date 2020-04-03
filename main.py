import sys
import packages.dataset_tools.generate_dataset as gen_da
from packages.dataset_tools.scale_dataset import split_dataset_by_obj_count as splt_da
from packages.pipes import prefabs



def print_help():
    print("""
        Arguments allowed:

            pipes:
                '-pipe=dsk2db (more)' sets up pipeline disk -> db
                '-pipe=api2db (more)' sets up pipeline api -> db
                '-pipe=dsk2js (more)' sets up pipeline disk -> js
                '-pipe=api2js (more)' sets up pipeline api -> js

            dataset:
                '-getdataset' (more) specify dataset download
                '-scaledataset' () specify dataset scale

            more:
                '-track=word1,word2,wordN' specifies API track
                '-path=./...' specifies file location of dataset
                '-query=word1,word2,wordN' query for frontend. 

                '-ttime=INT' Specify total time for getdataset
                '-stime=INT' Specify slice time for getdataset

                '-sdiv=INT' Specify division count for scale dataset
                '-sin=' Specify input for scale dataset (file)
                '-sout=' Specify output for scale dataset (dir)
                

            Examples:
                -pipe=dsk2db -path=./...
                -pipe=api2db -track=to,and,from
                -pipe=dsk2js -path=./.. -query=help,me
                -pipe=api2js -track=to,and,from -query=help,me

                -getdataset -ttime=10 -stime=10 -track=virus -path=./
                -scaledataset -sdiv=2 -sin=.. -sout=..
                -scaledataset -sdiv=2 -sin=./200403-00_45_30--200403-00_45_38.zip -sout=./

    """)


def cmd_pt1(cmd):
    if "-pipe=dsk2db" in cmd:
        start_dsk2db(cmd)

    elif "-pipe=api2db" in cmd:
        start_api2db(cmd)

    elif "pipe=dsk2js" in cmd:
        start_dsk2js(cmd)

    elif "-pipe=api2js" in cmd:
        start_api2js(cmd)

    elif "-getdataset" in cmd:
        start_gen_dataset(cmd)
    
    elif "-scaledataset" in cmd:
        start_scale_dataset(cmd)

    else:
        print("command not found")
        print_help()



def parse_from_to_ws(cmd, from_str):
    cmd = cmd.split()

    from_index = None
    for i, item in enumerate(cmd):
        if from_str in item:
            from_index = i
            

    if from_index == None:
        print(f"not found: {cmd}")
        return None

    return cmd[from_index].replace(from_str, '')




def cmd_pt2_track(cmd):
    parsed = parse_from_to_ws(cmd, "-track=")
    if parsed: return parsed.split(",")
    else: return None

def cmd_pt2_path(cmd):
    return parse_from_to_ws(cmd, "-path=")


def cmd_pt2_query(cmd):
    parsed = parse_from_to_ws(cmd, "-query=")
    if parsed: return parsed.split(",")
    else: return None

def cmd_pt2_gd_time(cmd):
    parsed = parse_from_to_ws(cmd, "-ttime=")
    if parsed: 
        try:
            return int(parsed)
        except:
            return None
    else: return None

def cmd_pt2_gd_time_slice(cmd):
    parsed = parse_from_to_ws(cmd, "-stime=")
    if parsed: 
        try:
            return int(parsed)
        except:
            return None
    else: return None

def cmd_pt2_gs_divider(cmd):
    parsed = parse_from_to_ws(cmd, "-sdiv=")
    if parsed: 
        try:
            return int(parsed)
        except:
            return None
    else: return None

def cmd_pt2_gs_split_out(cmd):
    return parse_from_to_ws(cmd, "-sout=")

def cmd_pt2_gs_split_in(cmd):
    return parse_from_to_ws(cmd, "-sin=")




def start_dsk2db(cmd):
    path = cmd_pt2_path(cmd)
    if not path: 
        print('command error')
        print_help()
        return

    print("Starting pipeline dsk->db.")
    prefabs.get_pipeline_dsk_cln_simi_db(
        filepath=path
    ).run()


def start_api2db(cmd):
    track = cmd_pt2_track(cmd)
    if not track: 
        print('command error')
        print_help()
        return

    print("Starting pipeline api->db")
    prefabs.get_pipeline_api_cln_simi_db(
        api_track=track
    ).run()


def start_gen_dataset(cmd):
    total_time = cmd_pt2_gd_time(cmd)
    time_slices = cmd_pt2_gd_time_slice(cmd)
    track = track = cmd_pt2_track(cmd)
    path = cmd_pt2_path(cmd)

    if not total_time or not time_slices or not track or not path: 
        print('command error')
        print_help()
        return
    
    print(f"Starting dataset download to: {path}")
    gen_da.example(
        path=path,
        time_total=total_time,
        time_between_slices=time_slices,
        track=track
    )


def start_scale_dataset(cmd):
    divider = cmd_pt2_gs_divider(cmd)
    path = cmd_pt2_gs_split_in(cmd)
    output = cmd_pt2_gs_split_out(cmd)

    if not divider or not path or not output: 
        print('command error')
        print_help()
        return

    print(f"Starting dataset scale, output; {output}")
    splt_da(
        divider=divider,
        filename=path,
        out_dir=output
    )

    


def start_dsk2js(cmd):
    path = cmd_pt2_path(cmd)
    query = cmd_pt2_query(cmd)
    if not path or not query: 
        print('command error')
        print_help()
        return

    print("Starting pipeline dsk->js")
    prefabs.get_pipeline_dsk_cln_simi_js(
        filepath=path,
        initial_query=query
    )


def start_api2js(cmd):
    track = cmd_pt2_track(cmd)
    query = cmd_pt2_query(cmd)
    if not track or not query:
        print('command error')
        print_help()
        return

    print("Starting pipeline api->js")
    prefabs.get_pipeline_api_cln_simi_js(
        api_track=track,
        initial_query=query
    ).run()




def main():

    args = sys.argv[1:]
    cmd_pt1(' '.join(args))


main()

