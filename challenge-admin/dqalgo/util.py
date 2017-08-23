# -*- coding: utf-8 -*-
__author__ = 'n2m'

r_sc_func = """
sc_func <- function(data, c.o, score){
    if(sum(is.na(data))>0){
        idx_na <- which( is.na(data))
        idx_not_na <- which( as.logical(1-is.na(data)))
        data_na <- data[idx_na]
        data_not_na <- data[-idx_na]


        lco <- length(c.o)
        lsc <- length(score)
        idx <- c()
        c.o[lsc] <- c.o[lsc]+1
        datasc <- c()
        sc <- c()

        for(i in 1:(lsc-1)){
            idx <- which(data_not_na>=c.o[i] & data_not_na<c.o[i+1])

            lntd <- length(names(table(data_not_na[ idx ])))
            jdx <- list()

            for(j in 1:lntd){
                jthsc <- (as.numeric(names(table(data_not_na[ idx ]))[j]) - c.o[i]) / (c.o[i+1]-c.o[i]) * (score[i+1]-score[i]) + score[i]
                jdx[[i]] <- which(data_not_na == names(table(data_not_na[ idx ]))[j])
                datasc[ jdx[[i]] ] <- jthsc
            }
        }

        sc[idx_na] <- NA
        sc[idx_not_na] <- datasc
        return(sc)
    }else{
        lco <- length(c.o)
        lsc <- length(score)
        idx <- c()
        c.o[lsc] <- c.o[lsc]+1
        datasc <- c()
        sc <- c()

        for(i in 1:(lsc-1)){
            idx <- which(data>=c.o[i] & data<c.o[i+1])

            lntd <- length(names(table(data[ idx ])))
            jdx <- list()

            for(j in 1:lntd){
                jthsc <- (as.numeric(names(table(data[ idx ]))[j]) - c.o[i]) / (c.o[i+1]-c.o[i]) * (score[i+1]-score[i]) + score[i]
                jdx[[i]] <- which(data == names(table(data[ idx ]))[j])
                datasc[ jdx[[i]] ] <- jthsc
            }
        }

        sc <- datasc
        return(sc)
    }
}
"""