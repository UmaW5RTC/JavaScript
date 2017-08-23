# -*- coding: utf-8 -*-
__author__ = 'n2m'

r_algo = """
dc_dw_int <- (dc_dt_acc_1 + dc_dt_acc_2)/2
dc_dw_device <- apply(cbind(dc_dt_du_1*1.25, dc_dt_du_2*2.5, dc_dt_du_3*3.75, dc_dt_du_4*1.5, dc_dt_du_5*3, dc_dt_du_6*4.5, dc_dt_du_7, dc_dt_du_8, dc_dt_du_9),1,max)

# dc_dw_dm <- df_beh_pre #using the pre-survey question Q1


dc_dw_sns <- rowSums(cbind(dc_dt_snsuse_1, dc_dt_snsuse_2, dc_dt_snsuse_3, dc_dt_snsuse_4, dc_dt_snsuse_5, dc_dt_snsuse_6, dc_dt_snsuse_7, dc_dt_snsuse_8, dc_dt_snsuse_9, dc_dt_snsuse_10, dc_dt_snsuse_11, dc_dt_snsuse_12, dc_dt_snsuse_13))*(dc_dt_snsfriend)*(dc_dt_snscheck)
dc_dpi_quiz <- rowMeans(cbind(dc_dpi_quiz_1, dc_dpi_quiz_2, dc_dpi_quiz_3, dc_dpi_quiz_4, dc_dpi_quiz_5, dc_dpi_quiz_6))


dt_cong_a <- rowMeans(cbind(dt_cong_1, dt_cong_2, dt_cong_3, dt_cong_4, dt_cong_5, dt_cong_6, dt_cong_7))
dt_cong <- (dt_cong_a)/4*0.9 + (dc_oim_1-1)/2*0.1

dc_oi_quiz <-  rowMeans(cbind(dc_oi_quiz_1, dc_oi_quiz_2, dc_oi_quiz_3, dc_oi_quiz_4, dc_oi_quiz_5, dc_oi_quiz_6))


dc_se <- rowMeans(cbind(dc_selfefficacy_1, dc_selfefficacy_2, dc_selfefficacy_3, dc_selfefficacy_4, dc_selfefficacy_5))


dc_gc <- rowMeans(cbind(dc_global_2, dc_global_3, dc_global_4, dc_global_5))

dc_citizen_quiz <- rowMeans(cbind(dc_citizen_quiz_1, dc_citizen_quiz_2, dc_citizen_quiz_3, dc_citizen_quiz_4, dc_citizen_quiz_5))



S <- array()

# S <- cbind((dc_dw_int-1)*50, dc_dw_device*100/4.5, dc_dw_sns/2.34, (dc_dw_dm-1)/13*100, dc_dpi_quiz*100)
# colnames(S)[(ncol(S)-4):ncol(S)] <- c("dc_dw_int", "dc_dw_device", "dc_dw_sns", "dc_dw_dm", "dc_dpi_quiz")
S <- cbind((dc_dw_int-1)*50, dc_dw_device*100/4.5, dc_dw_sns/2.34, dc_dpi_quiz*100)
colnames(S)[(ncol(S)-4):ncol(S)] <- c("dc_dw_int", "dc_dw_device", "dc_dw_sns", "dc_dpi_quiz")

S <- cbind(S, dt_cong*100, dc_oi_quiz*100)
colnames(S)[(ncol(S)-1):ncol(S)] <- c("dt_cong", "dc_oi_quiz")

S <- cbind(S, (dc_se-1)*100/3, (dc_gc-1)*100/4, dc_citizen_quiz*100)
colnames(S)[(ncol(S)-2):ncol(S)] <- c("dc_se", "dc_gc", "dc_citizen_quiz")


S <- as.data.frame(S)

dc_identity_score <- S$dt_cong*0.5 +
                     S$dc_gc*0.2 +
                     (S$dc_dpi_quiz + S$dc_citizen_quiz + S$dc_oi_quiz)*0.1
"""