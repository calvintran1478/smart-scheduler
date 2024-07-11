<template>
  <ion-page>
    <ion-content class="ion-padding" fullscreen>
      <h1 class="schedulize">Schedulize</h1>
      <h2 class="subtext">Start optimizing your day.</h2>
      <div class="ion-text-center">
        <img src="/logo.png" alt="Schedulize Logo" class="logo" />
      </div>

      <div class="container">
        <ion-item>
          <ion-input v-model="email" label="Email"></ion-input>
        </ion-item>

        <ion-item>
          <ion-input
            v-model="password"
            label="Password"
            type="password"
          ></ion-input>
        </ion-item>

        <ion-button class="custom_button" @click="login">Log In</ion-button>

        <ion-button
          fill="clear"
          class="forgot-password"
          @click="redirectToResetPassword"
          >Forgot Password?</ion-button
        >

        <p class="register-text ion-text-center">Don't have an account yet?</p>
        <ion-button router-link="/register" class="custom_button">Register</ion-button>
      </div>
    </ion-content>
  </ion-page>
</template>

<script>
import {
  IonButton,
  IonLabel,
  IonInput,
  IonItem,
  IonContent,
  IonPage,
} from "@ionic/vue";
import { defineComponent } from "vue";
import { setCookie } from '../services/auth';
import { getDeviceId } from '../services/device';
export default defineComponent({
  components: { IonButton, IonLabel, IonInput, IonItem, IonContent, IonPage },
  data() {
    return {
      email: "",
      password: "",
    };
  },
  methods: {
    async login() {
      try {
        const deviceId = getDeviceId();
        const response = await fetch("http://localhost:8000/api/v1/users/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: this.email,
            password: this.password,
            device_id: deviceId,
          }),
        });
        if (!response.ok) {
          throw new Error("Login failed");
        }
        const data = await response.json();
        if (!data.access_token) {
          throw new Error("Did not receive token");
        }

        console.log("Login successful");
        // Redirect to homepage
        this.$router.push('/home');
      } catch (error) {
        console.error("Error during login:", error);
      }
    },
    redirectToResetPassword() {
      // TODO: reset password interface
    },
  },
});
</script>

<style scoped>
.logo {
  width: 250px;
  height: auto;
  margin: 10px auto;
  padding-top: 30px;
}

.container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.forgot-password {
  margin-top: 10px;
}

.custom_button {
  --background: #75f4c7;
  width: 300px;
  color: #000000;
  font-weight: bold;
}

.schedulize {
  padding-top: 30px;
  font-size: 30px;
  font-weight: bold;
  text-align: center;
}

.subtext {
  font-size: 20px;
  text-align: center;
}
</style>
