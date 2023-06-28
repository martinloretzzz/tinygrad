.section .text
.globl _kernel
_kernel:
pushq   %rbp
movq    %rsp, %rbp
subq    $184, %rsp
# AssemblyInstruction(op=<UOps.DEFINE_REGISTER: 10>, out=None, vin=[], arg=(dtypes.uint64, 'A', 15))
# AssemblyInstruction(op=<UOps.DEFINE_REGISTER: 10>, out=None, vin=[], arg=(dtypes.float, 'f', 12))
# AssemblyInstruction(op=<UOps.DEFINE_REGISTER: 10>, out=None, vin=[], arg=(dtypes.int, 'i', 4))
# AssemblyInstruction(op=<UOps.SPECIAL: 9>, out=%A0, vin=[], arg='buf0')
movq %rdi, -8(%rbp)
# AssemblyInstruction(op=<UOps.SPECIAL: 9>, out=%A1, vin=[], arg='buf1')
movq %rsi, -16(%rbp)
# AssemblyInstruction(op=<UOps.SPECIAL: 9>, out=%A2, vin=[], arg='buf2')
movq %rdx, -24(%rbp)
# AssemblyInstruction(op=<UOps.SPECIAL: 9>, out=%A3, vin=[], arg='buf3')
movq %rcx, -32(%rbp)
# AssemblyInstruction(op=<UOps.CONST: 5>, out=%f0, vin=[], arg=-inf)
movl $0xFF800000, -124(%rbp)
# AssemblyInstruction(op=<UOps.CONST: 5>, out=%i0, vin=[], arg=0)
movl $0x0, -172(%rbp)
# AssemblyInstruction(op=<UOps.CAST: 8>, out=%A4, vin=[%i0], arg=None)
movslq -172(%rbp), %rax
movq %rax, -40(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%A5, vin=[%A4, %A2], arg=<BinaryOps.ADD: 1>)
movq -40(%rbp), %rax
movq -24(%rbp), %rbx
addq %rbx, %rax
movq %rax, -48(%rbp)
# AssemblyInstruction(op=<UOps.LOAD: 3>, out=%f1, vin=[%A5], arg=(0, 'global'))
movq -48(%rbp), %rbx
movl 0(%rbx), %eax
movl %eax, -128(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%A6, vin=[%A4, %A3], arg=<BinaryOps.ADD: 1>)
movq -40(%rbp), %rax
movq -32(%rbp), %rbx
addq %rbx, %rax
movq %rax, -56(%rbp)
# AssemblyInstruction(op=<UOps.LOAD: 3>, out=%f2, vin=[%A6], arg=(0, 'global'))
movq -56(%rbp), %rbx
movl 0(%rbx), %eax
movl %eax, -132(%rbp)
# AssemblyInstruction(op=<UOps.CONST: 5>, out=%i1, vin=[], arg=4)
movl $0x4, -176(%rbp)
# AssemblyInstruction(op=<UOps.CAST: 8>, out=%A7, vin=[%i1], arg=None)
movslq -176(%rbp), %rax
movq %rax, -64(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%A8, vin=[%A7, %A3], arg=<BinaryOps.ADD: 1>)
movq -64(%rbp), %rax
movq -32(%rbp), %rbx
addq %rbx, %rax
movq %rax, -72(%rbp)
# AssemblyInstruction(op=<UOps.LOAD: 3>, out=%f3, vin=[%A8], arg=(0, 'global'))
movq -72(%rbp), %rbx
movl 0(%rbx), %eax
movl %eax, -136(%rbp)
# AssemblyInstruction(op=<UOps.CONST: 5>, out=%i2, vin=[], arg=8)
movl $0x8, -180(%rbp)
# AssemblyInstruction(op=<UOps.CAST: 8>, out=%A9, vin=[%i2], arg=None)
movslq -180(%rbp), %rax
movq %rax, -80(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%A10, vin=[%A9, %A3], arg=<BinaryOps.ADD: 1>)
movq -80(%rbp), %rax
movq -32(%rbp), %rbx
addq %rbx, %rax
movq %rax, -88(%rbp)
# AssemblyInstruction(op=<UOps.LOAD: 3>, out=%f4, vin=[%A10], arg=(0, 'global'))
movq -88(%rbp), %rbx
movl 0(%rbx), %eax
movl %eax, -140(%rbp)
# AssemblyInstruction(op=<UOps.CONST: 5>, out=%i3, vin=[], arg=12)
movl $0x12, -184(%rbp)
# AssemblyInstruction(op=<UOps.CAST: 8>, out=%A11, vin=[%i3], arg=None)
movslq -184(%rbp), %rax
movq %rax, -96(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%A12, vin=[%A11, %A3], arg=<BinaryOps.ADD: 1>)
movq -96(%rbp), %rax
movq -32(%rbp), %rbx
addq %rbx, %rax
movq %rax, -104(%rbp)
# AssemblyInstruction(op=<UOps.LOAD: 3>, out=%f5, vin=[%A12], arg=(0, 'global'))
movq -104(%rbp), %rbx
movl 0(%rbx), %eax
movl %eax, -144(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%f6, vin=[%f1, %f2], arg=<BinaryOps.SUB: 2>)
movd -128(%rbp), %xmm0
subss -132(%rbp), %xmm0
movd %xmm0, -148(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%f7, vin=[%f1, %f3], arg=<BinaryOps.SUB: 2>)
movd -128(%rbp), %xmm0
subss -136(%rbp), %xmm0
movd %xmm0, -152(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%f8, vin=[%f1, %f4], arg=<BinaryOps.SUB: 2>)
movd -128(%rbp), %xmm0
subss -140(%rbp), %xmm0
movd %xmm0, -156(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%f9, vin=[%f1, %f5], arg=<BinaryOps.SUB: 2>)
movd -128(%rbp), %xmm0
subss -144(%rbp), %xmm0
movd %xmm0, -160(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%f0, vin=[%f0, %f6], arg=<BinaryOps.MAX: 7>)
movd -124(%rbp), %xmm0
maxss -148(%rbp), %xmm0
movd %xmm0, -124(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%f0, vin=[%f0, %f7], arg=<BinaryOps.MAX: 7>)
movd -124(%rbp), %xmm0
maxss -152(%rbp), %xmm0
movd %xmm0, -124(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%f0, vin=[%f0, %f8], arg=<BinaryOps.MAX: 7>)
movd -124(%rbp), %xmm0
maxss -156(%rbp), %xmm0
movd %xmm0, -124(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%f0, vin=[%f0, %f9], arg=<BinaryOps.MAX: 7>)
movd -124(%rbp), %xmm0
maxss -160(%rbp), %xmm0
movd %xmm0, -124(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%A13, vin=[%A4, %A1], arg=<BinaryOps.ADD: 1>)
movq -40(%rbp), %rax
movq -16(%rbp), %rbx
addq %rbx, %rax
movq %rax, -112(%rbp)
# AssemblyInstruction(op=<UOps.LOAD: 3>, out=%f10, vin=[%A13], arg=(0, 'global'))
movq -112(%rbp), %rbx
movl 0(%rbx), %eax
movl %eax, -164(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%f11, vin=[%f10, %f0], arg=<BinaryOps.SUB: 2>)
movd -164(%rbp), %xmm0
subss -124(%rbp), %xmm0
movd %xmm0, -168(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%A14, vin=[%A4, %A0], arg=<BinaryOps.ADD: 1>)
movq -40(%rbp), %rax
movq -8(%rbp), %rbx
addq %rbx, %rax
movq %rax, -120(%rbp)
# AssemblyInstruction(op=<UOps.STORE: 7>, out=None, vin=[%A14, %f11], arg=(0, 'global'))
movl -168(%rbp), %eax
movq -120(%rbp), %rbx
movl %eax, 0(%rbx)
leave
ret