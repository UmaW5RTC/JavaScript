# -*- coding: utf-8 -*-
__author__ = 'n2m'

r_algo = """
Y <- cbind(bst_screen_video_sd_1, bst_screen_video_sd_2, bst_screen_video_sd_3, bst_screen_video_sd_4, bst_screen_video_sd_5, bst_screen_video_sd_6, bst_screen_video_sd_7, bst_screen_video_sd_8, bst_screen_video_sd_9, bst_screen_video_sd_10,
            bst_screen_video_sd_11, bst_screen_video_sd_12, bst_screen_video_sd_13, bst_screen_video_sd_14, bst_screen_video_sd_15, bst_screen_video_sd_16, bst_screen_video_sd_17, bst_screen_video_sd_18, bst_screen_video_sd_19, bst_screen_video_sd_20,
            bst_screen_video_sd_21, bst_screen_video_sd_22, bst_screen_video_sd_23, bst_screen_video_sd_24,
            bst_screen_game_sd_1, bst_screen_game_sd_2, bst_screen_game_sd_3, bst_screen_game_sd_4, bst_screen_game_sd_5, bst_screen_game_sd_6, bst_screen_game_sd_7, bst_screen_game_sd_8, bst_screen_game_sd_9, bst_screen_game_sd_10,
            bst_screen_game_sd_11, bst_screen_game_sd_12, bst_screen_game_sd_13, bst_screen_game_sd_14, bst_screen_game_sd_15, bst_screen_game_sd_16, bst_screen_game_sd_17, bst_screen_game_sd_18, bst_screen_game_sd_19, bst_screen_game_sd_20,
            bst_screen_game_sd_21, bst_screen_game_sd_22, bst_screen_game_sd_23, bst_screen_game_sd_24,
            bst_screen_sns_sd_1, bst_screen_sns_sd_2, bst_screen_sns_sd_3, bst_screen_sns_sd_4, bst_screen_sns_sd_5, bst_screen_sns_sd_6, bst_screen_sns_sd_7, bst_screen_sns_sd_8, bst_screen_sns_sd_9, bst_screen_sns_sd_10,
            bst_screen_sns_sd_11, bst_screen_sns_sd_12, bst_screen_sns_sd_13, bst_screen_sns_sd_14, bst_screen_sns_sd_15, bst_screen_sns_sd_16, bst_screen_sns_sd_17, bst_screen_sns_sd_18, bst_screen_sns_sd_19, bst_screen_sns_sd_20,
            bst_screen_sns_sd_21, bst_screen_sns_sd_22, bst_screen_sns_sd_23, bst_screen_sns_sd_24,
            bst_screen_video_wd_1, bst_screen_video_wd_2, bst_screen_video_wd_3, bst_screen_video_wd_4, bst_screen_video_wd_5, bst_screen_video_wd_6, bst_screen_video_wd_7, bst_screen_video_wd_8, bst_screen_video_wd_9, bst_screen_video_wd_10,
            bst_screen_video_wd_11, bst_screen_video_wd_12, bst_screen_video_wd_13, bst_screen_video_wd_14, bst_screen_video_wd_15, bst_screen_video_wd_16, bst_screen_video_wd_17, bst_screen_video_wd_18, bst_screen_video_wd_19, bst_screen_video_wd_20,
            bst_screen_video_wd_21, bst_screen_video_wd_22, bst_screen_video_wd_23, bst_screen_video_wd_24,
            bst_screen_game_wd_1, bst_screen_game_wd_2, bst_screen_game_wd_3, bst_screen_game_wd_4, bst_screen_game_wd_5, bst_screen_game_wd_6, bst_screen_game_wd_7, bst_screen_game_wd_8, bst_screen_game_wd_9, bst_screen_game_wd_10,
            bst_screen_game_wd_11, bst_screen_game_wd_12, bst_screen_game_wd_13, bst_screen_game_wd_14, bst_screen_game_wd_15, bst_screen_game_wd_16, bst_screen_game_wd_17, bst_screen_game_wd_18, bst_screen_game_wd_19, bst_screen_game_wd_20,
            bst_screen_game_wd_21, bst_screen_game_wd_22, bst_screen_game_wd_23, bst_screen_game_wd_24,
            bst_screen_sns_wd_1, bst_screen_sns_wd_2, bst_screen_sns_wd_3, bst_screen_sns_wd_4, bst_screen_sns_wd_5, bst_screen_sns_wd_6, bst_screen_sns_wd_7, bst_screen_sns_wd_8, bst_screen_sns_wd_9, bst_screen_sns_wd_10,
            bst_screen_sns_wd_11, bst_screen_sns_wd_12, bst_screen_sns_wd_13, bst_screen_sns_wd_14, bst_screen_sns_wd_15, bst_screen_sns_wd_16, bst_screen_sns_wd_17, bst_screen_sns_wd_18, bst_screen_sns_wd_19, bst_screen_sns_wd_20,
            bst_screen_sns_wd_21, bst_screen_sns_wd_22, bst_screen_sns_wd_23, bst_screen_sns_wd_24)
colnames(Y)

Y_screen <- rbind(Y, Y)


Y_screensd <- Y_screen[,grep("_sd_", colnames(Y_screen))]
Y_screensd_video <- Y_screensd[,grep("video",colnames(Y_screensd))]
Y_screensd_game <- Y_screensd[,grep("game",colnames(Y_screensd))]
Y_screensd_sns <- Y_screensd[,grep("sns",colnames(Y_screensd))]
Y_screensd_vgs <- cbind(Y_screensd_video, Y_screensd_game, Y_screensd_sns)
sdmax <- 0
for(i in 1:24){
    sdmax <- sdmax + apply(Y_screensd_vgs[,grep(i,colnames(Y_screensd_vgs))], 1, max)
}
bst_tst_sd <- sdmax[1]

Y_screenwd <- Y_screen[,grep("_wd_", colnames(Y_screen))]
Y_screenwd_video <- Y_screenwd[,grep("video",colnames(Y_screenwd))]
Y_screenwd_game <- Y_screenwd[,grep("game",colnames(Y_screenwd))]
Y_screenwd_sns <- Y_screenwd[,grep("sns",colnames(Y_screenwd))]
Y_screenwd_vgs <- cbind(Y_screenwd_video, Y_screenwd_game, Y_screenwd_sns)
wdmax <- 0
for(i in 1:24){
    wdmax <- wdmax + apply(Y_screenwd_vgs[,grep(i,colnames(Y_screenwd_vgs))], 1, max)
}
bst_tst_wd <- wdmax[1]

dc_dw_device <- apply(cbind(dc_dt_du_1*1.25, dc_dt_du_2*2.5, dc_dt_du_3*3.75, dc_dt_du_4*1.5, dc_dt_du_5*3, dc_dt_du_6*4.5, dc_dt_du_7, dc_dt_du_8, dc_dt_du_9),1,max)
bst_tst_0 <- (bst_tst_sd)*5 + (bst_tst_wd)*2
bst_tst_1 <- replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(bst_tst_0, bst_tst_0>=0&bst_tst_0<15, 9), bst_tst_0>=15&bst_tst_0<30,8), bst_tst_0>=30&bst_tst_0<40,7), bst_tst_0>=40&bst_tst_0<50,6), bst_tst_0>=50&bst_tst_0<60,5), bst_tst_0>=60&bst_tst_0<70, 4), bst_tst_0>=70&bst_tst_0<80,3), bst_tst_0>=80&bst_tst_0<90,2), bst_tst_0>=90&bst_tst_0<100,1), bst_tst_0>=100,0)
dvweight = array()
dvweight[dc_dt_du_5 & dc_dt_du_6 == 1] = 1.1
dvweight[rowSums(cbind(dc_dt_du_1, dc_dt_du_2, dc_dt_du_3, dc_dt_du_4, dc_dt_du_5, dc_dt_du_6))==0 & rowSums(cbind(dc_dt_du_7, dc_dt_du_8, dc_dt_du_9)) > 0] = 0.9
dvweight[is.na(dvweight)] = 1
bst_tst <- bst_tst_1*dvweight


bst_ga <- 1-rowMeans(cbind(bst_ga_1, bst_ga_2, bst_ga_3, bst_ga_4, bst_ga_5, bst_ga_6, bst_ga_7, bst_ga_8, bst_ga_9, bst_ga_10, bst_ga_11))


bst_gameday_0 <- rowSums(cbind(bst_gameday_1, bst_gameday_2, bst_gameday_3, bst_gameday_4, bst_gameday_5, bst_gameday_6, bst_gameday_7))
bst_gameday <- replace(replace(replace(bst_gameday_0,bst_gameday_0<=3,3),(bst_gameday_0>3)&(bst_gameday_0<=5),2), bst_gameday_0>5,1)
bst_gametime <- as.numeric(bst_gametime_1==1)*3 + as.numeric(bst_gametime_1==2)*3 + as.numeric(bst_gametime_1==3)*2 + as.numeric(bst_gametime_1==4) + as.numeric(bst_gametime_1==5)
bst_gamewhen <- as.numeric(bst_gamewhen_4!=1)*(as.numeric(rowSums( cbind(bst_gamewhen_1, bst_gamewhen_2, bst_gamewhen_3))==3)*1.5 +
        as.numeric(bst_gamewhen_4!=1)*(as.numeric((rowSums(cbind(bst_gamewhen_1, bst_gamewhen_2, bst_gamewhen_3))==2) | (rowSums(cbind(bst_gamewhen_1, bst_gamewhen_2, bst_gamewhen_3))==1) ) )*2) +
        as.numeric(bst_gamewhen_4==1)
bst_gametime_rule <- bst_gameday * bst_gametime * bst_gamewhen
bst_sns_rule <- rowMeans(cbind(bst_fmp_1, (bst_fmp_2-1)/2, (bst_fmp_3-1)/2, (bst_fmp_4-1)/2, bst_fmp_0))
bst_priority <- rowMeans(cbind(dc_pri_1, dc_pri_2, dc_pri_3, dc_pri_4))
bst_sr <- rowMeans(cbind(bst_sr_1, bst_sr_2, bst_sr_3, bst_sr_4, bst_sr_5))


bst_quiz <- rowMeans(cbind(bst_quiz_1, bst_quiz_2, bst_quiz_3, bst_quiz_4, bst_quiz_5, bst_quiz_6, bst_quiz_7, bst_quiz_8, bst_quiz_9, bst_quiz_10, bst_quiz_11, bst_quiz_12, bst_quiz_13, bst_quiz_14, bst_quiz_15, bst_quiz_16, bst_quiz_17))


S <- array()

S <- cbind(bst_tst*10)
colnames(S)[ncol(S)] <- c("bst_tst")

S <- cbind(S, bst_ga*100)
colnames(S)[ncol(S)] <- "bst_ga"

S <- cbind(S, (bst_sr-1)*100/3, (bst_gametime_rule-1)*100/17, bst_sns_rule*100, bst_priority*100)
colnames(S)[(ncol(S)-3):ncol(S)] <- c("bst_sr", "bst_gametime_rule", "bst_sns_rule", "bst_priority")

S <- cbind(S, bst_quiz*100)
colnames(S)[ncol(S)] <- "bst_quiz"

S <- as.data.frame(S)

sc_mgmt_score <- S$bst_tst*0.2 +
                 (S$bst_ga)*0.3 +
                 S$bst_sr*0.2 +
                 (S$bst_gametime_rule + S$bst_sns_rule)*0.04
                 S$bst_priority*0.02
                 S$bst_quiz*0.2
"""