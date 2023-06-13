import json
from examples.compile_efficientnet import compile_net
from models.efficientnet import EfficientNet
from tinygrad.tensor import Tensor
from tinygrad.jit import TinyJit

if __name__ == "__main__":
  model = EfficientNet(0)
  model.load_from_pretrained()

  @TinyJit
  def run(x): return model.forward(x).realize()

  # @TinyJit
  # def run(x): 
  #   y = Tensor([[1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4]])
  #   return (y + (2 * x)).realize()

  # twice to run the JIT
  the_input = Tensor.randn(1,3,224,224) # 16
  the_output = run(the_input)
  the_output = run(the_input)

  # hack to put the inputs back
  assert len(run.input_replace) == 1, f"didn't get one input to replace {run.input_replace}"
  for (j,i),idx in run.input_replace.items():
    run.jit_cache[j][1][i] = the_input.lazydata.realized

  # TODO: fetch this from the jit in self.input_replace and self.ret (hint: use get_parameters on self.ret)
  special_names = {id(the_input.lazydata.realized): "input", id(the_output.lazydata.realized): "outputs"}

  functions, statements, bufs, bufs_to_save = compile_net(run, special_names, lambda name, cargs, global_size: {'kernel': name, 'args': cargs, 'global_size': global_size})
  print(functions)
  #print(statements)
  #print(bufs)
  #print(bufs_to_save)

  save_buf = {name: ''.join(["\\x%02X"%x for x in bytes(cl._buf)]) for name,cl in bufs_to_save.items()}

  with open('examples/net.json', 'w') as fp:
    json.dump({'functions': functions, 'statements': statements, 'bufs': bufs, 'bufs_to_save': save_buf}, fp)
