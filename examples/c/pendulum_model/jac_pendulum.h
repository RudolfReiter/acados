/* This file was automatically generated by CasADi.
   The CasADi copyright holders make no ownership claim of its contents. */
#ifdef __cplusplus
extern "C" {
#endif

#ifndef casadi_real
#define casadi_real double
#endif

#ifndef casadi_int
#define casadi_int int
#endif

int jacFun(const casadi_real** arg, casadi_real** res, casadi_int* iw, casadi_real* w, void* mem);
void jacFun_incref(void);
void jacFun_decref(void);
casadi_int jacFun_n_in(void);
casadi_int jacFun_n_out(void);
const char* jacFun_name_in(casadi_int i);
const char* jacFun_name_out(casadi_int i);
const casadi_int* jacFun_sparsity_in(casadi_int i);
const casadi_int* jacFun_sparsity_out(casadi_int i);
int jacFun_work(casadi_int *sz_arg, casadi_int* sz_res, casadi_int *sz_iw, casadi_int *sz_w);
#ifdef __cplusplus
} /* extern "C" */
#endif
