<template>
  <ion-page>
    <ion-content class="ion-padding">
      <div class="container">
        <h1 class="title">Your day, optimized.</h1>
        <ion-grid>
          <ion-row>
            <ion-col size="6">
              <ion-button fill="clear" expand="block" router-link="/timetable" class="home-button">
                <ion-icon :icon="calendarOutline" class="home-icon"></ion-icon>
                <ion-label class="home-label">Timetable</ion-label>
              </ion-button>
            </ion-col>
            <ion-col size="6">
              <ion-button fill="clear" expand="block" router-link="/pomodoro" class="home-button">
                <ion-icon :icon="timerOutline" class="home-icon"></ion-icon>
                <ion-label class="home-label">Pomodoro</ion-label>
              </ion-button>
            </ion-col>
          </ion-row>
          <ion-row>
            <ion-col size="6">
              <ion-button fill="clear" expand="block" router-link="/tasks" class="home-button">
                <ion-icon :icon="checkmarkDoneOutline" class="home-icon"></ion-icon>
                <ion-label class="home-label">Tasks</ion-label>
              </ion-button>
            </ion-col>
            <ion-col size="6">
              <ion-button fill="clear" expand="block" router-link="/habits" class="home-button">
                <ion-icon :icon="repeatOutline" class="home-icon"></ion-icon>
                <ion-label class="home-label">Habits</ion-label>
              </ion-button>
            </ion-col>
          </ion-row>
          <ion-row>
            <ion-col size="6">
              <ion-button fill="clear" expand="block" router-link="/settings" class="home-button">
                <ion-icon :icon="settingsOutline" class="home-icon"></ion-icon>
                <ion-label class="home-label">Settings</ion-label>
              </ion-button>
            </ion-col>
            <ion-col size="6">
              <ion-button fill="clear" expand="block" router-link="/analytics" class="home-button">
                <ion-icon :icon="analyticsOutline" class="home-icon"></ion-icon>
                <ion-label class="home-label">Analytics</ion-label>
              </ion-button>
            </ion-col>
          </ion-row>
        </ion-grid>
      </div>
    </ion-content>
  </ion-page>
</template>

<script>
import {
  IonButton,
  IonContent,
  IonPage,
  IonGrid,
  IonRow,
  IonCol,
  IonIcon,
  IonLabel
} from "@ionic/vue";
import { defineComponent } from "vue";
import {
  calendarOutline,
  timerOutline,
  checkmarkDoneOutline,
  repeatOutline,
  settingsOutline,
  analyticsOutline
} from "ionicons/icons";

export default defineComponent({
  components: {
    IonButton,
    IonContent,
    IonPage,
    IonGrid,
    IonRow,
    IonCol,
    IonIcon,
    IonLabel
  },
  data() {
    return {
      calendarOutline,
      timerOutline,
      checkmarkDoneOutline,
      repeatOutline,
      settingsOutline,
      analyticsOutline
    };
  }
});
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.title {
  padding-top: 30px;
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 20px;
}

.home-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 150px;
  margin: 10px 0;
}

.home-icon {
  font-size: 70px;
  color: #fff;
}

.home-label {
  margin-top: 10px;
  font-size: 16px;
  color: #fff;
}
</style>
