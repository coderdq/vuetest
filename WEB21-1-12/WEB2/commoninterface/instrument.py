import logging
import pyvisa

logger = logging.getLogger('ghost')


class Instrument(object):
    def __init__(self, ip):
        address = 'TCPIP::{}::INSTR'.format(ip)
        self.rm, self.inst = self.get_inst(address)

    def get_inst(self, adress):
        rm = pyvisa.ResourceManager()
        # res = rm.list_resources()
        inst = rm.get_instrument(adress)
        return rm, inst

    def get_handler(self):
        return self.inst

    def __del__(self):
        try:
            try:
                self.inst.close()
            except:
                pass
            try:
                self.rm.close()
            except:
                pass
        except Exception as e:
            logger.error(e)
            print('inst error {}'.format(e))
        finally:
            self.inst=None
            self.rm=None

class InstBase(object):
    def __init__(self,name):
        self.inst = None
        self.handle = None
        self.addr = None
        self.name=name

    def get_inst_name(self):
        return self.name

    def init_inst(self, addr):
        self.addr = addr
        try:
            if hasattr(self, 'inst'):
                try:
                    del self.inst
                except Exception as e:
                    logger.error(e)
            self.inst = Instrument(addr)
            self.handle = self.inst.get_handler()
            logger.debug('handle={}'.format(self.handle))
        except Exception:
            raise ModuleNotFoundError('{} not online'.format(self.name))
        if self.handle is None:
            raise ModuleNotFoundError('{} not online'.format(self.name))

    def close_inst(self):
        if hasattr(self, 'inst'):
            try:
                del self.inst
            except Exception:
                pass
        self.inst = Instrument(self.addr)
        del self.inst

    def init_again(self):
        try:
            if hasattr(self, 'inst'):
                try:
                    del self.inst
                except Exception:
                    pass
            self.inst = Instrument(self.addr)
            self.handle = self.inst.get_handler()
            logger.debug('handle={}'.format(self.handle))
        except:
            raise ModuleNotFoundError('{} not online'.format(self.name))
        if self.handle is None:
            raise ModuleNotFoundError('{} not online'.format(self.name))

    def ext_error_checking(self):
        if self.handle:
            errors = self.ext_check_error_queue()
            if errors is not None and len(errors) > 0:
                print('ext_error_checking')
                raise RuntimeError(errors)

    def ext_check_error_queue(self):
        errors = []
        stb = int(self.handle.query('*STB?'))
        if (stb & 4) == 0:
            return errors

        while True:
            response = self.handle.query('SYST:ERR?')
            if '"no error"' in response.lower():
                break
            errors.append(response)
            if len(errors) > 50:
                # safety stop
                errors.append('Cannot clear the error queue')
                break
        if len(errors) == 0:
            return None
        else:
            return errors

    def ext_query_bin_data_to_file(self, query, pc_file_path):
        if self.handle:
            file_data = self.handle.query_binary_values(query, datatype='s')[0]
            new_file = open(pc_file_path, "wb")
            new_file.write(file_data)
            new_file.close()

if __name__=='__main__':
    address = 'TCPIP::{}::INSTR'.format('192.168.1.11')
    rm = pyvisa.ResourceManager()
    rm.get_instrument(address).close()
