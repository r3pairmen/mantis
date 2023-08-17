from mantis.utils.common_utils import CommonUtils
from subprocess import Popen, PIPE
from mantis.models.args_model import ArgsModel
import logging
import sys
import time

class ToolScanner:
    
    def __init__(self) -> None:
        self.org = None
        self.base_command = None
        self.outfile_extension = None
        self.commands_list = []
        self.assets = []
        self.std = sys.stdout


    async def init(self, args:ArgsModel):
        return await self.get_commands(args=args)
    

    def get_commands(self, args: ArgsModel):
        raise NotImplementedError


    def base_get_commands(self, assets) :
        ## Return the list of commands
        command_list = []
        for every_asset in assets:  
            domain = every_asset
            outfile = CommonUtils.generate_unique_output_file_name(domain, self.outfile_extension)
            command = self.base_command.format(input_domain = domain, output_file_path = outfile)
            command_list.append((self, command, outfile, every_asset))
        self.commands_list = command_list
        return command_list
    
    
    def parse_report(self, outfile):
        raise NotImplementedError
    

    async def db_operations(self, tool_output_dict, asset=None):
        raise NotImplementedError
    

    async def execute(self, tool_tuple):
        results = {}
        command, outfile, asset = tool_tuple[1:]
        logging.debug(f"Command to be executed - {command}")
        logging.debug(f"Executing command - {command}")
        
        if self.std == "PIPE":
            stderr = PIPE
            stdout = PIPE
        else:
            stderr = sys.stderr
            stdout = sys.stdout

        code = 1
        try:
            start = time.perf_counter()

            subprocess_obj = Popen(
                command, stderr=stderr, stdout=stdout, shell=True) 
            code = subprocess_obj.wait()
            output,errors = subprocess_obj.communicate()

            finish = time.perf_counter()

            results["code"] = code
            results["output"] = output
            results["errors"] = errors
            results["asset"] = asset
            results["command"] = command
            results["success"] = 0
            results["failure"] = 0
            results["command_exec_time"] = round(finish - start, 2)
            logging.debug(f"Subprocess output - Code {code}, Errors {errors}")
            if code == 0: 
                results["success"] += 1
            else:
                results["failure"] += 1
            tool_results_dict = self.parse_report(outfile=outfile)
            if tool_results_dict:
                await self.db_operations(tool_results_dict, asset=asset)
        except Exception as e:
            results["exception"] = str(e)
            logging.exception(
                f"Error received: {type(e).__name__}: {e} for {asset} in tool {type(self).__name__}")
      
        return results