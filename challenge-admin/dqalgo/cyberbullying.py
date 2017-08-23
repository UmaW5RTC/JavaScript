# -*- coding: utf-8 -*-
__author__ = 'n2m'

r_algo = """
cb_cbbeh_rawscore0 <- rowSums(cbind(cb_cbbeh_1, cb_cbbeh_2, cb_cbbeh_3, cb_cbbeh_4, cb_cbbeh_5, cb_cbbeh_6, cb_cbbeh_7, cb_cbbeh_8, cb_cbbeh_9))
cb_cbbeh_rawscore1 <- 900-rowSums(cbind(cb_cbbeh_1, cb_cbbeh_2, cb_cbbeh_3, cb_cbbeh_4, cb_cbbeh_5, cb_cbbeh_6, cb_cbbeh_7, cb_cbbeh_8, cb_cbbeh_9))
cb_cbatt <- rowMeans(cbind(cb_cbatt_1, cb_cbatt_2, cb_cbatt_3, cb_cbatt_4, cb_cbatt_5))

cb_cbmgmt_talk <- rowSums(cbind(cb_cbmgmt_4*2.5, cb_cbmgmt_5*2, cb_cbmgmt_6, cb_cbmgmt_7*1.5))
cb_cbmgmt_react <- rowSums(cbind(cb_cbmgmt_3*2, cb_cbmgmt_10*2, cb_cbmgmt_8, cb_cbmgmt_1*0.5, cb_cbmgmt_2*(-1), cb_cbmgmt_9*(-2)))

cb_speakup <- cb_speakup_1

cb_quiz <- rowMeans(cbind(cb_quiz_1, cb_quiz_2, cb_quiz_3, cb_quiz_4, cb_quiz_5, cb_quiz_6, cb_quiz_7, cb_quiz_8, cb_quiz_9, cb_quiz_10, cb_quiz_11, cb_quiz_12, cb_quiz_13, cb_quiz_14, cb_quiz_15, cb_quiz_16, cb_quiz_17, cb_deal_34))


S <- array()

S <- cbind(replace(sc_func(cb_cbbeh_rawscore1,c(0,800,850,895,899),c(0,10,20,30,40)),which(cb_cbbeh_rawscore1==900),100), cb_cbatt*100/25)
colnames(S)[(ncol(S)-1):ncol(S)] <- c("cb_cbbeh_rawscore1", "cb_cbatt")

S <- cbind(S, cb_cbmgmt_talk*100/7, sc_func(cb_cbmgmt_react, c(-3,-1,1,3,4,5), c(0,20,40,60,80,100)), (cb_speakup-1)*25, cb_quiz*100)
colnames(S)[(ncol(S)-3):ncol(S)] <- c("cb_cbmgmt_talk", "cb_cbmgmt_react", "cb_speakup", "cb_quiz")


S <- as.data.frame(S)

cb_score <- S$cb_cbbeh_rawscore1*0.4 +
            S$cb_cbatt*0.1 +
            S$cb_cbmgmt_talk*0.135 +
            S$cb_cbmgmt_react*0.135 +
            S$cb_speakup*0.03 +
            S$cb_quiz*0.2
"""