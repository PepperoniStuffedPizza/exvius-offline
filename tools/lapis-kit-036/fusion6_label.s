    .text
    .globl _start
_start:
d1:
    cmp w23, #6
    adrp x2, fmt
    add x2, x2, :lo12:fmt
    csel x2, x2, x25, eq
    mov w3, w23
    b R1
d2:
    cmp w23, #6
    adrp x2, fmt
    add x2, x2, :lo12:fmt
    csel x2, x2, x25, eq
    mov w3, w23
    b R2
fmt: .asciz "sort_label_nvstart_s%2$d.png"
    .balign 4
