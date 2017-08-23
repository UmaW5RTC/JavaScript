# -*- coding: utf-8 -*-
__author__ = 'n2m'

r_algo = """
pme_v1 <- ct_mv_v_2 * ct_mv_v_3
vme_v1 <- ct_mv_v_2 * ct_mv_v_4
pme_v2 <- ct_mv_v_b_2 * ct_mv_v_b_3
vme_v2 <- ct_mv_v_b_2 * ct_mv_v_b_4
pme_g1 <- ct_mv_g_2 * apply(cbind(ct_mv_g_3, ct_mv_g_4),1,max)
vme_g1 <- ct_mv_g_2 * apply(cbind(ct_mv_g_5, ct_mv_g_6),1,max)
pme_g2 <- ct_mv_g_b_2 * apply(cbind(ct_mv_g_b_3, ct_mv_g_b_4),1,max)
vme_g2 <- ct_mv_g_b_2 * apply(cbind(ct_mv_g_b_5, ct_mv_g_b_6),1,max)
ct_pmp_v <- rowMeans(cbind(pme_v1, pme_v2))
ct_pmp_g <- rowMeans(cbind(pme_g1, pme_g2))
ct_vmp_v <- rowMeans(cbind(vme_v1, vme_v2))
ct_vmp_g <- rowMeans(cbind(vme_g1, vme_g2))
ct_mv <- ct_pmp_v + ct_pmp_g - ct_vmp_v - ct_vmp_g

ct_inapp_beh <- 12.5-(ct_inapp_1*1 + ct_inapp_2*1.5 + ct_inapp_3*2 + ct_inapp_4*2 + ct_inapp_5 + ct_inapp_6*2.5 + ct_inapp_7*2.5)

ct_block_unwanted <- rowMeans(cbind(ct_block_a_1, ct_block_a_2, ct_block_a_3, ct_block_a_4, ct_block_a_5, ct_block_a_6, ct_block_a_7, ct_inapp_c))

ct_content_quiz <- rowMeans(cbind( ct_content_quiz_1, ct_content_quiz_2, ct_content_quiz_3, ct_content_quiz_4, ct_content_quiz_5 ))


ct_ie_quiz <- rowMeans(cbind( ct_ie_quiz_1, ct_ie_quiz_3, ct_ie_quiz_5, ct_ie_quiz_6, ct_ie_quiz_7, ct_ie_quiz_8, ct_ie_quiz_9, ct_ie_quiz_10, ct_ie_quiz_11, ct_ie_quiz_12, ct_ie_quiz_13, ct_ie_quiz_14, ct_ie_quiz_15 ))


ct_of_chat_1[ct_of_chat_1==2]=1
ct_ofm_beh_1[ct_ofm_beh_1==2]=1
ct_of_chat <- ct_of_chat_1*35
beforetell <- 2*(ct_ofm_tell1_1 + ct_ofm_tell1_2) + rowSums(cbind(ct_ofm_tell1_3, ct_ofm_tell1_4, ct_ofm_tell1_5))
bring <- 4*(ct_ofm_bring_1 + ct_ofm_bring_2) + 3*rowSums(cbind(ct_ofm_tell1_3, ct_ofm_tell1_4, ct_ofm_tell1_5))
aftertell <- 2*(ct_ofm_tell2_1 + ct_ofm_tell2_2) + rowSums(cbind(ct_ofm_tell1_3, ct_ofm_tell1_4, ct_ofm_tell1_5))
ct_ofm_beh <- as.numeric(ct_ofm_beh_1==0)*(beforetell + bring + aftertell)
ct_ofm_beh[which(ct_ofm_beh_1==1)] <- 35

ct_of_beh <- (ct_ofm_beh+ct_of_chat)/2
ct_of_att <- ct_ofm_att_2
ct_ofc_strat <- (4*(cb_of_a_2) + 2*(cb_of_a_3 + cb_of_a_6) + 3*(cb_of_a_1) + (cb_of_a_4 + cb_of_a_7) + 0*(cb_of_a_5))/2 + (ct_contact_risk)/2
ct_ofm_strat <- 4*ct_ofm_st_2 + 2*ct_ofm_st_3 + 3*ct_ofm_st_1 + 3*ct_ofm_st_5 + 0*ct_ofm_st_4 + ct_ofm_st_6 + 0*ct_ofm_st_7
ct_contact_quiz <- rowMeans(cbind( ct_contact_quiz_2, ct_contact_quiz_3, ct_contact_quiz_4, ct_contact_quiz_5, ct_contact_quiz_6 ))


S <- array()

S <- cbind(S, sc_func(ct_mv,c(-48,-12.5,-5,0,5,12.5,48),c(0,100/6,200/6,300/6,400/6,500/6,100)), sc_func(ct_inapp_beh, c(0,7,11,12.5), c(0,25,50,100)), ct_content_quiz, (ct_block_unwanted+1)*100/2)
colnames(S)[(ncol(S)-3):ncol(S)] <- c("ct_mv", "ct_inapp_beh", "ct_content_quiz", "ct_block_unwanted")

S <- cbind(S, ct_ie_quiz*100)
colnames(S)[ncol(S)] <- c("ct_ie_quiz")

S <- cbind(S, ct_of_beh*100/35, (ct_of_att-1)*25, ct_contact_quiz*20, ct_ofc_strat*100/8.5, ct_ofm_strat*100/13)
colnames(S)[(ncol(S)-4):ncol(S)] <- c("ct_of_beh", "ct_of_att", "ct_contact_quiz", "ct_ofc_strat", "ct_ofm_strat")

S <- as.data.frame(S)


ct_score <- S$ct_mv*0.33*2/9 +
            S$ct_inapp_beh*0.33/9 +
            S$ct_content_quiz*0.33/3 +
            S$ct_block_unwanted*0.33/3 +
            S$ct_ie_quiz*0.34 +
            S$ct_of_beh*0.33*2/9 +
            S$ct_of_att*0.33*1/9 +
            S$ct_contact_quiz*0.33/3 +
            S$ct_ofc_strat*0.33/6 +
            S$ct_ofm_strat*0.33/6
"""