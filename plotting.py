from __future__ import print_function

import numpy as np
import pandas
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes, mark_inset, inset_axes

global offset
offset = 0

power = 0.2
def bincl(ell, cl, clerr, nbins=10):
    clerr = np.mean(clerr, axis=0)
    if len(ell) > nbins:
        ells = np.array_split(ell, nbins)
        cls = np.array_split(cl, nbins)
        sigmas = np.array_split(clerr, nbins)
        ellb = np.array([l.mean() for l in ells])
        clb = np.array([sum(cl/sig**2)/sum(1/sig**2) for cl, sig in zip(cls, sigmas)])
        errb = np.array([1/sum(1/sig**2) for sig in sigmas])**0.5
        ellwidth = np.array([l[-1] - l[0] for l in ells])/2*0
    else:
        ellb = ell
        clb = cl
        errb = clerr
        ellwidth = np.zeros_like(ell)
    return ellwidth, ellb, clb, errb

class Plotting(object):

    def __init__(self, title=None, degreescale=False, inset=False):
        self.data = {}
        self.data['TT'] = CMBData('TT_data_2017feb_csv_format.dat', 'TT')
        self.data['EE'] = CMBData('EE_data_2016dec_csv_format.dat', 'EE')
        self.data['TE'] = CMBData('TE_data_2016dec_csv_format.dat', 'TE')
        self.data['BB'] = CMBData('BB_data_2015nov_csv_format.dat', 'BB')
        self.data['lensing'] = CMBData('lensing_data_2017jan_csv_format.dat', '')
       
        self.load_theory()
        
        self.degreescale = degreescale
        self.inset = inset

        self.fig = plt.figure(tight_layout=True)

        self.ax = self.fig.add_subplot(1, 1, 1)
        
        if self.degreescale:
            self.ax2 = self.ax.twiny()

        if title is not None:
            self.fig.suptitle(title)
        
        #if self.degreescale and title is not None:
        #    self.fig.subplots_adjust(hspace=0.3)

        if inset:
            self.axins = inset_axes(self.ax, 1.5, 1, loc=4)
            self.axins.set_xlim(2, 100)
            self.axins.set_ylim(-0.2, 1)
            self.axins.tick_params(
                axis='both',          # changes apply to the x-axis
                which='both',      # both major and minor ticks are affected
                bottom='off',      # ticks along the bottom edge are off
                top='off',         # ticks along the top edge are off
                left='off',
                right='off',
                labelbottom='off',
                labelleft='off')

        self.xlabel(r'$\ell$', string2=r'Angle ($^\circ$)')
        self.ylabel(r'$\sqrt{\frac{\ell (\ell+1)}{2\pi}C_\ell}$ ($\mathrm{\mu K}$)')
         
        self.xlim([2, 1500])

        self.llp1 = None

    def load_theory(self):
       
        self.theory = {}
        tmp = np.loadtxt('base_plikHM_TT_lowTEB.minimum.theory_cl')


        '''
        theory_lensCl = np.loadtxt('B2_3yr_camb_planck_lensed_uK_20140314.txt')
        theory_inf = np.loadtxt('B2_3yr_camb_planck_withB_uK_20140314.txt')
        self.theory['TT'] = np.array([theory_inf[:,0], theory_inf[:, 1]])
        self.theory['EE'] = np.array([theory_inf[:,0], theory_inf[:, 3]])
        self.theory['TE'] = np.array([theory_inf[:,0], theory_inf[:, 2]])

        self.theory['BB-inf'] = np.array([theory_inf[:,0], theory_inf[:, 4]])
        self.theory['BB-lens'] = np.array([theory_lensCl[:,0], theory_lensCl[:, 4]])

        '''
        import camb
        lmax = 4000
        pars = camb.CAMBparams()

        pars.InitPower.set_params(ns=0.9619, As=2.12e-9, r=0.00)
        pars.set_cosmology(H0=66.93, ombh2=0.02218, omch2=0.1205, mnu=0.06, omk=0,
                tau=0.0596)
        pars.set_for_lmax(lmax, lens_potential_accuracy=1)
        results = camb.get_results(pars)
        results.Params.Max_l = lmax
        powers = results.get_cmb_power_spectra(pars)
        T0 = pars.TCMB*1e6
        theory_lensCl = powers['total']*T0**2
        theory_lensCl = theory_lensCl[:4001]
        ell = np.arange(len(theory_lensCl[:,0]))

        pars.InitPower.set_params(ns=0.9616, As=2.12e-9, r=0.07)
        pars.set_for_lmax(lmax, lens_potential_accuracy=0)
        pars.AccurateReionization = 1
        pars.AccurateBB = 1
        pars.NonLinear = 2
        pars.WantTensors = True
        pars.DoLensing = 0
        pars.max_l_tensor = 8000
        pars.max_eta_k_tensor = 16000
        results = camb.get_results(pars)
        pars.set_for_lmax(lmax, max_eta_k=100000, lens_potential_accuracy=1)


        
        pars.set_cosmology(H0=66.93, ombh2=0.02218, omch2=0.1205, mnu=0.06, omk=0,
                tau=0.0596)
        pars.set_for_lmax(lmax, lens_potential_accuracy=1)
        results = camb.get_results(pars)
        results.Params.Max_l = lmax
        powers = results.get_cmb_power_spectra(pars)
        T0 = pars.TCMB*1e6
        theory_inf = powers['total']*T0**2

        self.theory['TT'] = np.array([ell, theory_inf[:, 0]])
        self.theory['EE'] = np.array([ell, theory_inf[:, 1]])
        self.theory['TE'] = np.array([ell, theory_inf[:, 3]])

        self.theory['BB-inf'] = np.array([ell, theory_inf[:, 2]])
        self.theory['BB-lens'] = np.array([ell, theory_lensCl[:, 2]])




        self.theory['lensing'] = np.array([tmp[:, 0], tmp[:, 5]*1e7])

    def plot_measurement(self, experiment, cltype, color='b', bins=None, 
            label=None, doub=False, symbol='o', nbins=10):
        '''Plot the power spectrum measurements for a given
        experiment'''

        data = self.data[cltype]

        ell_center, ell_minus, ell_plus, binval, sigma_plus, sigma_minus, upper_bound = data.get_data(experiment)
        sigmas = np.array([sigma_plus, sigma_minus])
        
        if label is None:
            label = experiment

        #if ell_minus != np.array(None):
        #    xerr = np.array([ell_minus, ell_plus])
        #else:
        #    #xerr = None
        #    xerr = np.zeros_like(sigmas)

        xerr = np.array([ell_minus, ell_plus])

        if bins is not None:
            ell_center = ell_center[bins]
            binval = binval[bins]
            upper_bound = upper_bound[bins]
            xerr = xerr[:, bins]
            sigmas = sigmas[:, bins]
            sigma_minus = sigma_minus[bins]

        #Determine points to plot as error bars and ones to plot as upperbounds
        if doub:
            i_ub = (sigma_minus > binval) | np.isnan(binval)
            i_bin = ~i_ub
        else:
            i_bin = np.isfinite(binval)
            i_ub = i_bin & False

        #Plot errorbars
        ms = 7
        alpha = 0.8
        if np.any(i_bin):
            #self.ax.errorbar(ell_center[i_bin], binval[i_bin], xerr=xerr[:,
            #    i_bin], yerr=sigmas[:, i_bin], color=color, fmt='o',
            #    label=label, ms=ms, alpha=alpha)
            #self.ax.errorbar(ell_center[i_bin], -binval[i_bin], xerr=xerr[:,
            #    i_bin], yerr=sigmas[:, i_bin], markeredgecolor=color, fmt='o',
            #    markerfacecolor='none', label=label, ms=ms, alpha=alpha)
            xerr, ellb, clb, errb = bincl(ell_center[i_bin], binval[i_bin], 
                                                sigmas[:,i_bin], nbins=nbins)
            inds = np.where(ellb > 45)

            self.ax.errorbar(ellb[inds]**power, clb[inds]**0.5, xerr=xerr[inds],
                    yerr=0.5*errb[inds]/abs(clb[inds])**0.5, fmt=symbol,
                    #yerr=errb[inds], fmt=symbol,
                    ms=ms,
                color=color, alpha=alpha)
            self.ax.errorbar(ellb[inds]**power, (-clb[inds])**0.5, xerr=xerr[inds],
                    yerr=0.5*errb[inds]/abs(clb[inds])**0.5, fmt=symbol, markerfacecolor='none', 
                    #yerr=errb[inds], fmt=symbol, markerfacecolor='none', 
                    ms=ms, markeredgecolor=color, markeredgewidth=1,
                    ecolor=color, alpha=alpha)
            inds = np.where(ellb <= 45)
            if len(inds) > 0:
                #print(ell_center[i_bin][inds], binval[i_bin][inds],
                #        sigmas[:,i_bin])
                #print(inds, ellb, sigmas, sigmas[:,inds[0]].shape)
                if cltype=='TT':
                    nbins = 1000
                else:
                    nbins = 4
                xerr, ellb, clb, errb = bincl(ell_center[i_bin][inds],
                        binval[i_bin][inds], sigmas[:,i_bin][:,inds[0]],
                        nbins=nbins)
                if np.any(np.array([clb])) == 0:
                    norm = 0.5*errb
                    clb = 0.5*errb
                else:
                    norm = 0.5*errb/abs(clb)**0.5
                    clb = clb
                jitter = 1+np.random.random(len(ellb))*0.05
                self.ax.errorbar(jitter*ellb**power, clb**0.5,
                        yerr=norm, fmt=symbol,
                        ms=ms, color=color, alpha=alpha)
                self.ax.errorbar(jitter*ellb**power, (-clb)**0.5,
                        yerr=norm, fmt=symbol, markerfacecolor='none',
                        ms=ms, markeredgecolor=color, markeredgewidth=1,
                        ecolor=color, alpha=alpha)
            label=None
            if self.inset:
                self.axins.errorbar(ell_center[i_bin], binval[i_bin],
                        xerr=[xerr[:, i_bin]], yerr=sigmas[:,
                            i_bin], color=color,
                        fmt=symbol, label=label, ms=ms, alpha=alpha)
                self.axins.errorbar(ell_center[i_bin], -binval[i_bin],
                        xerr=xerr[:, i_bin], yerr=sigmas[:,
                            i_bin],
                        markeredgecolor=color, markerfacecolor='none',
                        fmt=symbol,
                        label=label, ms=ms, alpha=alpha)
            '''
            for j in range(len(ell_center[i_bin])):
                alpha = binval[i_bin][j]/max(sigmas[:, i_bin][:,j])
                alpha = abs(alpha)/6
                if alpha > 1:
                    alpha = 1
                #alpha = alpha**2
                self.ax.errorbar(ell_center[i_bin][j], binval[i_bin][j], xerr=[xerr[:,
                    i_bin][:,j]], yerr=[sigmas[:, i_bin][:,j]], color=color, fmt='o',
                    label=label, ms=ms, alpha=alpha)
                self.ax.errorbar(ell_center[i_bin][j], -binval[i_bin][j], xerr=[xerr[:,
                    i_bin][:,j]], yerr=[sigmas[:, i_bin][:,j]], markeredgecolor=color, fmt='o',
                    markerfacecolor='none', label=label, ms=ms, alpha=alpha)
                label=None
                if self.inset:
                    self.axins.errorbar(ell_center[i_bin][j], binval[i_bin][j],
                            xerr=[xerr[:, i_bin][:,j]], yerr=[sigmas[:,
                                i_bin][:,j]], color=color,
                            fmt='o', label=label, ms=ms, alpha=alpha)
                    self.axins.errorbar(ell_center[i_bin][j], -binval[i_bin][j],
                            xerr=[xerr[:, i_bin][:,j]], yerr=[sigmas[:,
                                i_bin][:,j]],
                            markeredgecolor=color, markerfacecolor='none', fmt='o',
                            label=label, ms=ms, alpha=alpha)
            '''

        if np.any(i_ub):
            self.ax.errorbar(ell_center[i_ub], upper_bound[i_ub]**0.5, xerr=xerr[:, i_ub], yerr=sigmas[:, i_ub]/abs(upper_bound[i_ub])**0.5, color=color, fmt='o', label=label,
                             uplims=True, ms=ms)
            self.ax.errorbar(ell_center[i_ub], (-upper_bound[i_ub])**0.5, xerr=xerr[:,
                i_ub], yerr=sigmas[:, i_ub]/abs(upper_bound[i_ub])**0.5, fmt='o', label=label,
                markerfacecolor='none', markeredgecolor=color, uplims=True,
                ms=ms)
            print(ell_center[i_ub], upper_bound[i_ub], sigmas[:,i_ub])


        
        #self.ax.legend(loc=0, prop={'size': 12})

    def list_experiments(self, cltype):
        '''Returns a list of the different experiments for which we
        have results given the input cltype'''

        experiments = self.data[cltype].experiments()

        print(experiments)

    def plot_theory(self, cltype, color, r=0.01, log=False, llp1=None):

        lw = 1

        if cltype != 'BB':
            ell = self.theory[cltype][0]
        else:
            nell_a = len(self.theory['BB-inf'][0])
            nell_b = len(self.theory['BB-lens'][0])
            nell = min(nell_a, nell_b)
            ell = self.theory['BB-inf'][0]

        if llp1 is None and self.llp1 is None:
            llp1 = True
            self.llp1 = True
        elif llp1 is None:
            llp1 = self.llp1
        elif self.llp1 is None:
            self.llp1 = llp1
        elif self.llp1 != llp1:
            raise ValueError("Requested normalization does not match previous plotted lines")

        if self.llp1:
            fact = 1
        else:
            fact = ell*(ell+1) / 2*np.pi
        
        linestyle = '-'

        if 'BB' not in cltype:
            cl_theory = self.theory[cltype][1] / fact
        elif cltype == 'BB':
            cl_inf = r/0.1*self.theory['BB-inf'][1][:nell]
            cl_lens = self.theory['BB-lens'][1][:nell]
            cl_theory = cl_inf + cl_lens
            cl_theory /= fact
            linestyle = ':'
        elif cltype == 'BB-inf':
            cl_theory = r/0.1*self.theory[cltype][1] / fact
        elif cltype == 'BB-lens':
            cl_theory = self.theory[cltype][1] / fact
            linestyle = '--'
        else:
            raise ValueError('cltype is not valid')

        if cltype == 'TE':
            der = (np.diff(cl_theory)/np.diff(ell))[1:]/cl_theory[2:]
            ignore = np.where(der > 0.3)
            cl_theory[ignore] = np.nan

        if log:
            self.ax.loglog(ell[2:]**power, cl_theory[2:]**0.5, color, linestyle=linestyle,
                    lw=lw)
            self.ax.loglog(ell[2:]**power, (-cl_theory[2:])**0.5, color, linestyle='-.', lw=lw)
        else:
            self.ax.plot(ell[2:]**power, cl_theory[2:]**0.5, color, linestyle=linestyle,
                    lw=lw)
            self.ax.plot(ell[2:]**power, (-cl_theory[2:])**0.5, color, linestyle='-.', lw=lw)


        if self.inset:
            self.axins.semilogx(ell[2:], cl_theory[2:], color)

        print(cltype, (cl_theory[2]*2*np.pi/(2*3))**0.5)

    def xlabel(self, string, string2=None):
        '''Sets the xlabel of the plot'''
        self.ax.set_xlabel(string)

        if string2 is not None and self.degreescale:
            self.ax2.set_xlabel(string2)
    
    def ylabel(self, string):
        '''Sets the xlabel of the plot'''
        self.ax.set_ylabel(string)

    def title(self, string):
        self.ax.set_title(string)

    def xlim(self, val):
        self.ax.set_xlim(val)

        if self.degreescale:
            val2 = [180.0/val[0], 180.0/val[1]]
            self.ax2.set_xlim(val2)

    def ylim(self, val):
        self.ax.set_ylim(val)

    def set_axes(self, xscale='linear', yscale='linear'):
        self.ax.set_xscale(xscale)
        self.ax.set_yscale(yscale)
        if self.degreescale:
            self.ax2.set_xscale(xscale)

    def default_BB_plot(self):
        '''Generate a default BB plot with most of the current measurements plotted'''

        self.plot_theory('BB', 'C3', r=0.07)
        self.plot_theory('BB-lens', 'C3')
        self.plot_theory('BB-inf', 'C3', r=0.07)

        self.plot_measurement('BICEP2+Keck', 'BB', color='C3', symbol='p')
        #self.plot_measurement('BICEP2+Keck/Planck', 'BB', color='C5')
        self.plot_measurement('POLARBEAR', 'BB', color='C3', symbol='s')
        self.plot_measurement('SPTpol', 'BB', color='C3', symbol='>')
        self.set_axes(xscale='log', yscale='log')
        self.xlim([2, 5000])
        self.ylim([1e-3, 0.6])

    def default_TT_plot(self):
        '''Generate a default TT plot'''

        self.plot_measurement('Planck_Plik_lite', 'TT', color='C0',
                label='Planck', symbol='^', nbins=1000)
        self.plot_measurement('Planck_COM_PowerSp', 'TT', color='C0',
                label='Planck', symbol='^', nbins=20)
        self.plot_measurement('WMAP_2013', 'TT', color='C0', label='WMAP 2013',
                symbol='v', nbins=1000)
        self.plot_measurement('ACTPol', 'TT', color='C0', symbol='<')
        self.plot_measurement('SPT', 'TT', color='C0', symbol='>')
        #self.plot_measurement('SPTPol', 'TT', color='C9')
        self.set_axes(xscale='log', yscale='log')
        self.plot_theory('TT', 'C0')
        self.xlim([2, 5000])
        self.ylim([0.05, 10000])

    def default_TE_plot(self):
        '''Generate a default TE plot'''

        self.plot_theory('TE', 'C1')
        #self.plot_measurement('WMAP_unbinned', 'TE', color='C9', label='WMAP 2013')
        self.plot_measurement('Planck_2015', 'TE', color='C1', 
            label='Planck 2015', symbol='^', nbins=15)
        self.plot_measurement('ACTPol_2016', 'TE', color='C1', label='ACTPol 2016', symbol='<')
        self.plot_measurement('WMAP_2013', 'TE', color='C1', label='WMAP 2013',
            symbol='v', nbins=15)
        self.plot_measurement('BICEP2/Keck_2015', 'TE', color='C1',
            label='BICEP2/Keck 2015', symbol='p')
        self.plot_measurement('SPTpol_2015', 'TE', color='C1', label='SPTPol 2015', symbol='>')
        self.set_axes(xscale='log', yscale='linear')
        self.xlim([2, 5000])
        self.ylim([-200, 200])
    
    def default_EE_plot(self):
        '''Generate a default EE plot'''

        self.plot_theory('EE', 'C2')
        self.plot_measurement('Planck_2015', 'EE', color='C2', 
                label='Planck 2015', symbol='^', nbins=15)#, nbins=10)
        self.plot_measurement('WMAP_2013', 'EE', color='C2', label='WMAP 2013',
            symbol='v', nbins=15)
        self.plot_measurement('ACTPol_2016', 'EE', color='C2', label='ACTPok 2016', symbol='<')
        self.plot_measurement('BICEP2/Keck_2015', 'EE', color='C2',
            label='BICEP2/Keck 2015', symbol='p')
        self.plot_measurement('SPTpol_2015', 'EE', color='C2', label='SPTPk 2016', symbol='>')
        self.set_axes(xscale='log', yscale='log')
        self.xlim([2, 5000])
        self.ylim([-5, 50])

    def default_lensing_plot(self):
        '''Generate a default dd plot'''

        self.plot_theory('lensing', 'k')
        self.plot_measurement('POLARBEAR_2014', 'lensing', color='C4', label='POLARBEAR 2014')
        self.plot_measurement('ACTPol_2016', 'lensing', color='C2', label='ACTPol 2016')
        self.plot_measurement('SPTpol_2015', 'lensing', color='C3', label='SPTPol 2015')
        self.set_axes(xscale='log', yscale='log')
        self.xlim([2, 5000])
        self.ylabel(r'$10^7 \ell (\ell+1) C_\ell / 2\pi$ ($\mu$K$^2$)')
        

class CMBData(object):

    def __init__(self, filename, datatype):
        self.data = pandas.read_csv(filename, comment='#', skipinitialspace=True)

        columns = self.data.columns

        #Remove the whitespace at the end of each column name
        self.data.rename(columns=lambda x: x.rstrip(), inplace=True)
        #for i in range(len(self.data['Experiment'])):
        #    #self.data.loc[:,('Experiment', i)] = self.data['Experiment'][i].rstrip()
        #    self.data['Experiment'][i] = self.data['Experiment'][i].rstrip()
        self.data['Experiment'] = self.data['Experiment'].str.strip()
        self.data['l_min'].astype(float)
        self.data['l_center'].astype(float)
        self.data['l_max'].astype(float)
        self.data['Power'].astype(float)
        self.data['Sigma_minus'].astype(float)
        self.data['Sigma_plus'].astype(float)
        self.data['Upper Limit'].astype(float)
        
        #self.datatype = datatype

        #if datatype != 'lensing':
        #    self.sigma_plus = 'sigma_' + datatype + '_plus'
        #    self.sigma_minus = 'sigma_' + datatype + '_minus'
        #    self.upper_bound = datatype + '_limit'
        #    self.binval = datatype
        #else:
        #    self.sigma_plus = 'sigma_power'
        #    self.sigma_minus = 'sigma_power'
        #    self.binval = 'power'
        
        if datatype == 'BB':
            self._eval_ub()

    def experiments(self):
        '''Return a list of experiments'''
        return list(set(self.data['Experiment']))

    def get_data(self, experiment):

        npts = len(self.data)
       
        datatype = 'Power'
        sigplus = 'Sigma_plus'
        sigminus = 'Sigma_minus'
        ub = 'Upper Limit'

        ell_center = []

        ell_minus = None
        ell_plus = None
        binval = []
        sigma_plus = []
        sigma_minus = []
        upper_bound = []
        for i in range(npts):
            if self.data['Experiment'][i] == experiment:
                ell_center.append(self.data['l_center'][i])
                binval.append(self.data['Power'][i])
                sigma_plus.append(self.data['Sigma_plus'][i])
                sigma_minus.append(self.data['Sigma_minus'][i])
                if 'l_min' in self.data.columns and 'l_max' in self.data.columns:
                    if ell_minus is None:
                        ell_minus = []
                    if ell_plus is None:
                        ell_plus = []
                    ell_minus.append(self.data['l_center'][i] - self.data['l_min'][i])
                    ell_plus.append(self.data['l_max'][i] - self.data['l_center'][i])
                upper_bound.append(self.data['Upper Limit'][i])
        
        return np.array(ell_center), np.array(ell_minus), np.array(ell_plus), np.array(binval), np.array(sigma_plus), np.array(sigma_minus), np.array(upper_bound)
    
    def _eval_ub(self):
        '''Adding in an upper bound for bins that might need it. Some experiments report
        measurements that are not very significant and people might want to plot these as
        upper limits.'''

        #upper_bound = self.data[self.upper_bound]
        #binval = self.data[self.binval]
        #sigma_minus = self.data[self.sigma_minus]
        #sigma_plus = self.data[self.sigma_plus]

        upper_bound = self.data['Upper Limit']
        binval = self.data['Power']
        sigma_minus = self.data['Sigma_minus']
        sigma_plus = self.data['Sigma_plus']

        #Points that don't already have an upper bound and are
        #not 2 sigma measurements
        idx = np.isnan(upper_bound) & (binval - 2*sigma_minus <= 0)

        pandas.options.mode.chained_assignment = None
        upper_bound[idx] = binval[idx] + 2*sigma_plus[idx]

        #Hopefully to deal with a possible issue in pandas where 
        #upper_bound is a copy of the data and
        #not the data itself
        self.data['Upper Limit'] = upper_bound

