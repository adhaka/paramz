#===============================================================================
# Copyright (c) 2012 - 2014, GPy authors (see AUTHORS.txt).
# Copyright (c) 2014, James Hensman, Max Zwiessele
# Copyright (c) 2015, Max Zwiessele
#
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# * Neither the name of paramax nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#===============================================================================

import datetime as dt
from scipy import optimize
from warnings import warn

from .scg import SCG

class Optimizer():
    """
    Superclass for all the optimizers.

    :param x_init: initial set of parameters
    :param f_fp: function that returns the function AND the gradients at the same time
    :param f: function to optimize
    :param fp: gradients
    :param messages: print messages from the optimizer?
    :type messages: (True | False)
    :param max_f_eval: maximum number of function evaluations

    :rtype: optimizer object.

    """
    def __init__(self, x_init, messages=False, model=None, max_f_eval=1e4, max_iters=1e3,
                 ftol=None, gtol=None, xtol=None, bfgs_factor=None):
        self.opt_name = None
        self.x_init = x_init
        # Turning messages off and using internal structure for print outs:
        self.messages = False #messages
        self.f_opt = None
        self.x_opt = None
        self.funct_eval = None
        self.status = None
        self.max_f_eval = int(max_iters)
        self.max_iters = int(max_iters)
        self.bfgs_factor = bfgs_factor
        self.trace = None
        self.time = "Not available"
        self.xtol = xtol
        self.gtol = gtol
        self.ftol = ftol
        self.model = model

    def run(self, **kwargs):
        start = dt.datetime.now()
        self.opt(**kwargs)
        end = dt.datetime.now()
        self.time = str(end - start)

    def opt(self, f_fp=None, f=None, fp=None):
        raise NotImplementedError("this needs to be implemented to use the optimizer class")

    def __str__(self):
        diagnostics = "Optimizer: \t\t\t\t %s\n" % self.opt_name
        diagnostics += "f(x_opt): \t\t\t\t %.3f\n" % self.f_opt
        diagnostics += "Number of function evaluations: \t %d\n" % self.funct_eval
        diagnostics += "Optimization status: \t\t\t %s\n" % self.status
        diagnostics += "Time elapsed: \t\t\t\t %s\n" % self.time
        return diagnostics

class opt_tnc(Optimizer):
    def __init__(self, *args, **kwargs):
        Optimizer.__init__(self, *args, **kwargs)
        self.opt_name = "TNC (Scipy implementation)"

    def opt(self, f_fp=None, f=None, fp=None):
        """
        Run the TNC optimizer

        """
        tnc_rcstrings = ['Local minimum', 'Converged', 'XConverged', 'Maximum number of f evaluations reached',
             'Line search failed', 'Function is constant']

        assert f_fp != None, "TNC requires f_fp"

        opt_dict = {}
        if self.xtol is not None:
            opt_dict['xtol'] = self.xtol
        if self.ftol is not None:
            opt_dict['ftol'] = self.ftol
        if self.gtol is not None:
            opt_dict['pgtol'] = self.gtol

        opt_result = optimize.fmin_tnc(f_fp, self.x_init, messages=self.messages,
                       maxfun=self.max_f_eval, **opt_dict)
        self.x_opt = opt_result[0]
        self.f_opt = f_fp(self.x_opt)[0]
        self.funct_eval = opt_result[1]
        self.status = tnc_rcstrings[opt_result[2]]

class opt_lbfgsb(Optimizer):
    def __init__(self, *args, **kwargs):
        Optimizer.__init__(self, *args, **kwargs)
        self.opt_name = "L-BFGS-B (Scipy implementation)"

    def opt(self, f_fp=None, f=None, fp=None):
        """
        Run the optimizer

        """
        rcstrings = ['Converged', 'Maximum number of f evaluations reached', 'Error']

        assert f_fp != None, "BFGS requires f_fp"

        if self.messages:
            iprint = 1
        else:
            iprint = -1

        opt_dict = {}
        if self.xtol is not None:
            print("WARNING: l-bfgs-b doesn't have an xtol arg, so I'm going to ignore it")
        if self.ftol is not None:
            print("WARNING: l-bfgs-b doesn't have an ftol arg, so I'm going to ignore it")
        if self.gtol is not None:
            opt_dict['pgtol'] = self.gtol
        if self.bfgs_factor is not None:
            opt_dict['factr'] = self.bfgs_factor

        opt_result = optimize.fmin_l_bfgs_b(f_fp, self.x_init, iprint=iprint,
                                            maxfun=self.max_iters, **opt_dict)
        self.x_opt = opt_result[0]
        self.f_opt = f_fp(self.x_opt)[0]
        self.funct_eval = opt_result[2]['funcalls']
        self.status = rcstrings[opt_result[2]['warnflag']]

        #a more helpful error message is available in opt_result in the Error case
        if opt_result[2]['warnflag']==2:
            self.status = 'Error' + str(opt_result[2]['task'])

class opt_simplex(Optimizer):
    def __init__(self, *args, **kwargs):
        Optimizer.__init__(self, *args, **kwargs)
        self.opt_name = "Nelder-Mead simplex routine (via Scipy)"

    def opt(self, f_fp=None, f=None, fp=None):
        """
        The simplex optimizer does not require gradients.
        """

        statuses = ['Converged', 'Maximum number of function evaluations made', 'Maximum number of iterations reached']

        opt_dict = {}
        if self.xtol is not None:
            opt_dict['xtol'] = self.xtol
        if self.ftol is not None:
            opt_dict['ftol'] = self.ftol
        if self.gtol is not None:
            print("WARNING: simplex doesn't have an gtol arg, so I'm going to ignore it")

        opt_result = optimize.fmin(f, self.x_init, (), disp=self.messages,
                   maxfun=self.max_f_eval, full_output=True, **opt_dict)

        self.x_opt = opt_result[0]
        self.f_opt = opt_result[1]
        self.funct_eval = opt_result[3]
        self.status = statuses[opt_result[4]]
        self.trace = None


class opt_SCG(Optimizer):
    def __init__(self, *args, **kwargs):
        if 'max_f_eval' in kwargs:
            warn("max_f_eval deprecated for SCG optimizer: use max_iters instead!\nIgnoring max_f_eval!", FutureWarning)
        Optimizer.__init__(self, *args, **kwargs)

        self.opt_name = "Scaled Conjugate Gradients"

    def opt(self, f_fp=None, f=None, fp=None):
        assert not f is None
        assert not fp is None

        opt_result = SCG(f, fp, self.x_init, display=self.messages,
                         maxiters=self.max_iters,
                         max_f_eval=self.max_f_eval,
                         xtol=self.xtol, ftol=self.ftol,
                         gtol=self.gtol)

        self.x_opt = opt_result[0]
        self.trace = opt_result[1]
        self.f_opt = self.trace[-1]
        self.funct_eval = opt_result[2]
        self.status = opt_result[3]
        
class Opt_Adadelta(Optimizer):
    def __init__(self, step_rate=0.1, decay=0.9, momentum=0, *args, **kwargs):
        Optimizer.__init__(self, *args, **kwargs)
        self.opt_name = "Adadelta (climin)"
        self.step_rate=step_rate
        self.decay = decay
        self.momentum = momentum

    def opt(self, f_fp=None, f=None, fp=None):
        assert not fp is None
        
        import climin
                    
        opt = climin.adadelta.Adadelta(self.x_init, fp, step_rate=self.step_rate, decay=self.decay, momentum=self.momentum)
        
        for info in opt:
            if info['n_iter']>=self.max_iters:
                self.x_opt =  opt.wrt
                self.status = 'maximum number of function evaluations exceeded '
                break

def get_optimizer(f_min):

    optimizers = {'fmin_tnc': opt_tnc,
          'simplex': opt_simplex,
          'lbfgsb': opt_lbfgsb,
          'scg': opt_SCG,
          'adadelta':Opt_Adadelta}

    for opt_name in optimizers.keys():
        if opt_name.lower().find(f_min.lower()) != -1:
            return optimizers[opt_name]

    raise KeyError('No optimizer was found matching the name: %s' % f_min)
