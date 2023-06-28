.section .text
.globl _kernel
_kernel:
	pushq	%rbp
	movq	%rsp, %rbp
	subq	$58, %rsp
# AssemblyInstruction(op=<UOps.DEFINE_REGISTER: 10>, out=None, vin=[], arg=(dtypes.uint64, 'A', 5))
# AssemblyInstruction(op=<UOps.DEFINE_REGISTER: 10>, out=None, vin=[], arg=(dtypes.int, 'i', 2))
# AssemblyInstruction(op=<UOps.DEFINE_REGISTER: 10>, out=None, vin=[], arg=(dtypes.float, 'f', 2))
# AssemblyInstruction(op=<UOps.DEFINE_REGISTER: 10>, out=None, vin=[], arg=(dtypes.bool, 'p', 1))
# AssemblyInstruction(op=<UOps.SPECIAL: 9>, out=%A0, vin=[], arg='buf0')
movq %rdi, -8(%rbp)
# AssemblyInstruction(op=<UOps.SPECIAL: 9>, out=%A1, vin=[], arg='buf1')
movq %rsi, -16(%rbp)
# AssemblyInstruction(op=<UOps.CONST: 5>, out=%i0, vin=[], arg=0)
movl $0x0, -44(%rbp)
# AssemblyInstruction(op=<UOps.LABEL: 11>, out=None, vin=[], arg='$loop_gidx0')
.loop_gidx0:
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%i1, vin=[%i0, 4], arg=<BinaryOps.MUL: 3>)
movl -44(%rbp), %eax
movl $4, %ebx
mull %ebx
movl %eax, -48(%rbp)
# AssemblyInstruction(op=<UOps.CAST: 8>, out=%A2, vin=[%i1], arg=None)
movslq -48(%rbp), %rax
movq %rax, -24(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%A3, vin=[%A2, %A1], arg=<BinaryOps.ADD: 1>)
movq -24(%rbp), %rax
movq -16(%rbp), %rbx
addq %rbx, %rax
movq %rax, -32(%rbp)
# AssemblyInstruction(op=<UOps.LOAD: 3>, out=%f0, vin=[%A3], arg=(0, 'global'))
movq -32(%rbp), %rbx
movl 0(%rbx), %eax
movl %eax, -52(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%f1, vin=[%f0], arg=<UnaryOps.SIN: 5>)
movd -52(%rbp), %xmm0
call sinf@PLT
movd %xmm0, -56(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%A4, vin=[%A2, %A0], arg=<BinaryOps.ADD: 1>)
movq -24(%rbp), %rax
movq -8(%rbp), %rbx
addq %rbx, %rax
movq %rax, -40(%rbp)
# AssemblyInstruction(op=<UOps.STORE: 7>, out=None, vin=[%A4, %f1], arg=(0, 'global'))
movl -56(%rbp), %eax
movq -40(%rbp), %rbx
movl %eax, 0(%rbx)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%p0, vin=[%i0, 2924], arg=<BinaryOps.CMPLT: 9>)
movl -44(%rbp), %eax
movl $3, %ebx
cmpl %ebx, %eax
setae %al
movl %eax, -58(%rbp)
# AssemblyInstruction(op=<UOps.ALU: 4>, out=%i0, vin=[%i0, 1], arg=<BinaryOps.ADD: 1>)
movl -44(%rbp), %eax
movl $1, %ebx
addl %ebx, %eax
movl %eax, -44(%rbp)
# AssemblyInstruction(op=<UOps.COND_BRANCH: 12>, out=None, vin=[%p0], arg=('$loop_gidx0', True))
movb -58(%rbp), %al
test %al, %al
je .loop_gidx0
leave
ret