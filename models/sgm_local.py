from spectrome import functions

import numpy as np
from sklearn.preprocessing import minmax_scale
from scipy.stats import pearsonr

import tensorflow as tf
import tensorflow_probability as tfp
tfd = tfp.distributions

# np.random.seed(111)
# tf.random.set_seed(111)

class sgm_local:
    def __init__(self, fvec):
        self._fvec = fvec

    
    def simulate(self, parameters):

        def network_transfer(params,w):
            tau_e = params[0]/1000
            tau_i = params[1]/1000
            gii = params[2]
            gei = params[3]
#             pw_scale = params[7]
            pw_scale = 1
            gee = 1


            # Cortical model
            Fe = np.divide(1 / tau_e ** 2, (1j * w + 1 / tau_e) ** 2)
            Fi = np.divide(1 / tau_i ** 2, (1j * w + 1 / tau_i) ** 2)

            Hed = (1 + (Fe * Fi * gei)/(tau_e * (1j * w + Fi * gii/tau_i)))/(1j * w + Fe * gee/tau_e + (Fe * Fi * gei)**2/(tau_e * tau_i * (1j * w + Fi * gii / tau_i)))
            
            Hid = (1 - (Fe * Fi * gei)/(tau_i * (1j * w + Fe * gee/tau_e)))/(1j * w + Fi * gii/tau_i + (Fe * Fi * gei)**2/(tau_e * tau_i * (1j * w + Fe * gee / tau_e)))

            Htotal = Hed + Hid
            
            return pw_scale*Htotal
        

        freq_mdl = []
        for freq in self._fvec:
            _w = 2 * np.pi * freq
            freq_model = network_transfer(parameters, _w)
            freq_mdl.append(freq_model)

        freq_mdl = np.transpose(np.asarray(freq_mdl))
        
        freq_out = functions.mag2db(np.abs(freq_mdl))
        
        return freq_out


# # # # # # # # # Probabilistic Model # # # # # # # # # # #    
class Probabilistic_SGMlocal(tf.keras.Model):
    def __init__(self, fvec, IC, name = None):
        super(Probabilistic_SGMlocal, self).__init__(name=name)
        self.SGM = sgm_local(fvec=fvec)
#         self.taue_shape = tf.Variable(tf.random.normal([1], mean = IC[0], stddev = 0.0001), name = 'tau_e_shape')
#         self.taue_scale = tf.Variable(tf.random.normal([1], mean = np.log(np.exp(0.008)-1), stddev = 0.1), name = 'tau_e_scale')
#         self.taui_shape = tf.Variable(tf.random.normal([1], mean = IC[1], stddev = 0.0001), name = 'tau_i_shape')
#         self.taui_scale = tf.Variable(tf.random.normal([1], mean = np.log(np.exp(0.005)-1), stddev = 0.1), name = 'tau_i_scale')
#         self.gii_shape = tf.Variable(tf.random.normal([1], mean = IC[2], stddev = 0.001), name = 'gii_shape')
#         self.gii_scale = tf.Variable(tf.random.normal([1], mean = np.log(np.exp(0.8)-1), stddev = 0.1), name = 'gii_scale')
#         self.gei_shape = tf.Variable(tf.random.normal([1], mean = IC[3], stddev = 0.001), name = 'gei_shape')
#         self.gei_scale = tf.Variable(tf.random.normal([1], mean = np.log(np.exp(0.8)-1), stddev = 0.1), name = 'gei_scale')
        self.taue_shape = tf.Variable(tf.random.normal([1], mean = IC[0]), name = 'tau_e_shape')
        self.taue_scale = tf.Variable(tf.random.normal([1], mean = 2), name = 'tau_e_scale')
        self.taui_shape = tf.Variable(tf.random.normal([1], mean = IC[1]), name = 'tau_i_shape')
        self.taui_scale = tf.Variable(tf.random.normal([1], mean = 2), name = 'tau_i_scale')
        self.gii_shape = tf.Variable(tf.random.normal([1], mean = IC[2]), name = 'gii_shape')
        self.gii_scale = tf.Variable(tf.random.normal([1], mean = 2), name = 'gii_scale')
        self.gei_shape = tf.Variable(tf.random.normal([1], mean = IC[3]), name = 'gei_shape')
        self.gei_scale = tf.Variable(tf.random.normal([1], mean = 2), name = 'gei_scale')
#         self.sigma_loc = tf.Variable(tf.random.normal([1]), name = 'sigma_loc')
#         self.sigma_scale = tf.Variable(tf.random.normal([1]), name = 'sigma_scale')
#         self.p_shape = tf.Variable(tf.random.normal([1], mean = 1e4), name = "p_shape")
#         self.p_scale = tf.Variable(tf.random.normal([1], mean=1e3), name = "p_scale")


    @property
    def qtaue(self):
        """Variational posterior for tau_e"""
        return tfd.Gamma(concentration = tf.nn.softplus(self.taue_shape), rate = tf.nn.softplus(self.taue_scale))
#         return tfd.Normal(tf.nn.softplus(self.taue_shape), tf.nn.softplus(self.taue_scale))
    
    @property
    def qtaui(self):
        """Variational posterior for tau_i"""
        return tfd.Gamma(concentration = tf.nn.softplus(self.taui_shape), rate = tf.nn.softplus(self.taui_scale))
#         return tfd.Normal(tf.nn.softplus(self.taui_shape), tf.nn.softplus(self.taui_scale))

    @property
    def qgii(self):
        """Variational posterior for gii"""
        return tfd.Gamma(concentration = tf.nn.softplus(self.gii_shape), rate = tf.nn.softplus(self.gii_scale))
#         return tfd.Normal(tf.nn.softplus(self.gii_shape), tf.nn.softplus(self.gii_scale))
    
    @property
    def qgei(self):
        """Variational posterior for gei"""
        return tfd.Gamma(concentration = tf.nn.softplus(self.gei_shape), rate = tf.nn.softplus(self.gei_scale))
#         return tfd.Normal(tf.nn.softplus(self.gei_shape), tf.nn.softplus(self.gei_scale))

#     @property
#     def qp(self):
#         """Variational posterior for p"""
#         # return tfd.Gamma(concentration = tf.nn.softplus(self.ae_shape), rate = tf.nn.softplus(self.ae_scale))
#         return tfd.Normal(tf.nn.softplus(self.p_shape), tf.nn.softplus(self.p_scale))

    @property
    def qstd(self):
        """Variational posterior for sigma"""
        # return tfd.LogNormal(loc = tf.nn.softplus(self.sigma_loc), scale = tf.nn.softplus(self.sigma_scale))
#         return tfd.Normal(tf.nn.softplus(self.sigma_loc), scale = tf.nn.softplus(self.sigma_scale))
#         return tfd.ExpInverseGamma(tf.exp(self.sigma_loc), tf.exp(self.sigma_scale))
#         return tfd.Gamma(tf.nn.softplus(self.sigma_loc), tf.nn.softplus(self.sigma_scale))
        return tfd.InverseGamma(tf.exp(tf.random.normal([1], mean = 1, stddev = 0.001)), tf.exp(tf.random.normal([1],mean=-0.7,stddev=0.001)))
        # return tfd.InverseGamma(tf.nn.softplus(tf.random.normal([1])), tf.nn.softplus(tf.random.normal([1])))


    def call(self, obs, sampling=True):
        """Predict p(y|theta)?"""
        sample = lambda x: x.sample().numpy() if sampling else x.mean()
        loglik = tf.zeros([])
        std = 0.14
#         print(self.qtaue.mean(),self.qtaui.mean(),self.qgii.mean(),self.qgei.mean())
        for i in range(1024):
            parameters = np.array([
                                    sample(self.qtaue),
                                    sample(self.qtaui),
                                    sample(self.qgii),
                                    sample(self.qgei)
    #                                 sample(self.qp),
                                    ])

            # Forward model simulation
            fullspectrum = self.SGM.simulate(parameters)
    #         std = tf.sqrt(sample(self.qstd))
#             std = 0.14
    #         loc = fullspectrum.astype('float32')
            loc = np.transpose(minmax_scale(fullspectrum).astype('float32'))
    #         print(loc.shape)
            density = tfd.Normal(loc, std)
            loglik += tf.reduce_mean(density.log_prob(obs))
        loglik = loglik/1024
        return loglik
        # print(tf.reduce_mean(density.log_prob(obs)))
#         return density.log_prob(obs)
#         return -pearsonr(obs, np.transpose(fullspectrum)[:,0])[0].astype('float32')


    @property
    def losses(self):
        """Sum of KL divergences between posterior and priors"""
#         prior_taue = tfd.Normal(0.01,0.008)
#         prior_taui = tfd.Normal(0.005,0.005)
#         prior_gii = tfd.Normal(1,0.8)
#         prior_gei = tfd.Normal(1,0.8)
        prior_taue = tfd.Gamma(10,2)
        prior_taui = tfd.Gamma(10,2)
        prior_gii = tfd.Gamma(2,2)
        prior_gei = tfd.Gamma(2,2)
#         prior_std = tfd.Normal(1,0.5)
#         prior_p = tfd.Normal(1e4,1e3)
#         prior_std = tfd.Gamma(1.0, 0.5)
#         prior_std = tfd.ExpInverseGamma(0.5, 0.5)
        # prior_std = tfd.LogNormal(loc = 0.5, scale = 0.5)
        return (tf.reduce_sum(tfd.kl_divergence(self.qtaue, prior_taue)) + 
                tf.reduce_sum(tfd.kl_divergence(self.qtaui, prior_taui)) + 
                tf.reduce_sum(tfd.kl_divergence(self.qgii, prior_gii)) + 
                tf.reduce_sum(tfd.kl_divergence(self.qgei, prior_gei))) 
#                 + 
#                 tf.reduce_sum(tfd.kl_divergence(self.qp, prior_p)))
