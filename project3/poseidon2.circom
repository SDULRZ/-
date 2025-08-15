pragma circom 2.1.4;
template Sbox() {
    signal input in;
    signal output out;
    signal t1, t2;
    t1 <== in * in;  
    t2 <== t1 * t1;    
    out <== t2 * in;
}
template FullRound(round_constants) {
    signal input state[3];
    signal output out[3];
    signal after_addRC[3];
    for (var i = 0; i < 3; i++) {
        after_addRC[i] <== state[i] + round_constants[i];
    }
    component sbox0 = Sbox();
    component sbox1 = Sbox();
    component sbox2 = Sbox();
    sbox0.in <== after_addRC[0];
    sbox1.in <== after_addRC[1];
    sbox2.in <== after_addRC[2];
    out[0] <== 5*sbox0.out + 7*sbox1.out + 1*sbox2.out;
    out[1] <== 3*sbox0.out + 2*sbox1.out + 8*sbox2.out;
    out[2] <== 6*sbox0.out + 4*sbox1.out + 9*sbox2.out;
}
template PartialRound(round_constants) {
    signal input state[3];
    signal output out[3];
    signal after_addRC[3];
    for (var i = 0; i < 3; i++) {
        after_addRC[i] <== state[i] + round_constants[i];
    }
    component sbox = Sbox();
    sbox.in <== after_addRC[0];
    out[0] <== 5*sbox.out + 7*after_addRC[1] + 1*after_addRC[2];
    out[1] <== 3*sbox.out + 2*after_addRC[1] + 8*after_addRC[2];
    out[2] <== 6*sbox.out + 4*after_addRC[1] + 9*after_addRC[2];
}
template Poseidon2() {
    signal input in[2]; 
    signal output out; 
    signal state[3];
    state[0] <== 0;
    state[1] <== 0;
    state[2] <== 0;
    state[0] <== in[0];
    state[1] <== in[1];
    var round_constants = [
        [1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], 
        [13, 14, 15], [16, 17, 18], [19, 20, 21],     
        [22, 23, 24], [25, 26, 27], [28, 29, 30],     
        [31, 32, 33], [34, 35, 36], [37, 38, 39]
    ];
    component full_rounds[4];
    for (var i = 0; i < 4; i++) {
        full_rounds[i] = FullRound(round_constants[i]);
        for (var j = 0; j < 3; j++) {
            if (i == 0) {
                full_rounds[i].state[j] <== state[j];
            } else {
                full_rounds[i].state[j] <== full_rounds[i-1].out[j];
            }
        }
    }
    component partial_rounds[5];
    for (var i = 0; i < 5; i++) {
        partial_rounds[i] = PartialRound(round_constants[4+i]);
        for (var j = 0; j < 3; j++) {
            if (i == 0) {
                partial_rounds[i].state[j] <== full_rounds[3].out[j];
            } else {
                partial_rounds[i].state[j] <== partial_rounds[i-1].out[j];
            }
        }
    }
    component last_rounds[4];
    for (var i = 0; i < 4; i++) {
        last_rounds[i] = FullRound(round_constants[9+i]);
        for (var j = 0; j < 3; j++) {
            if (i == 0) {
                last_rounds[i].state[j] <== partial_rounds[4].out[j];
            } else {
                last_rounds[i].state[j] <== last_rounds[i-1].out[j];
            }
        }
    }
    out <== last_rounds[3].out[0];
}
template Main() {
    signal input in[2];      
    signal output out;       
    component poseidon = Poseidon2();
    for (var i = 0; i < 2; i++) {
        poseidon.in[i] <== in[i];
    }
    out <== poseidon.out;
}
component main = Main();