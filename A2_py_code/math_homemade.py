class StatisticsMath:
    def CI_instant(self, gns, std, datapunkter): # Konfidensintervaller anvendes typisk kun med store datasæt
        # Beregner SEM først (standard error of mean)
        SEM = std / np.sqrt(datapunkter)
        # Calculates confidenceintervals
        CI_upper = gns+1.96*SEM
        CI_lower = gns-1.96*SEM

        return CI_upper, CI_lower 
    
    def t_test():
        pass

    def power_calculation():
        pass # Make Poweer calcuations

    def data_saturation_test():
        pass 
