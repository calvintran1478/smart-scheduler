<template>
  <ion-page>
    <ion-content class="ion-padding">
      <h1 class="schedulize">Schedulize</h1>
      <h2 class="subtext">Start optimizing your day.</h2>
      <div class="register-form">
        <form @submit.prevent="registerUser">
          <div class="form-group">
            <ion-label position="floating">First Name</ion-label>
            <ion-input v-model="firstName" type="text" required></ion-input>
          </div>
          <div class="form-group">
            <ion-label position="floating">Last Name</ion-label>
            <ion-input v-model="lastName" type="text" required></ion-input>
          </div>
          <div class="form-group">
            <ion-label position="floating">Email</ion-label>
            <ion-input v-model="email" type="email" required></ion-input>
          </div>
          <div class="form-group">
            <ion-label position="floating">Password</ion-label>
            <ion-input v-model="password" type="password" required></ion-input>
          </div>
          <div class="form-group">
            <ion-label position="floating">Confirm Password</ion-label>
            <ion-input
              v-model="confirmPassword"
              type="password"
              required
            ></ion-input>
          </div>
          <ion-button expand="block" type="submit" class="custom_button"
            >Register</ion-button
          >
        </form>
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
import { getDeviceId } from '../services/device';

export default defineComponent({
  components: { IonButton, IonLabel, IonInput, IonItem, IonContent, IonPage },
  data() {
    return {
      firstName: "",
      lastName: "",
      email: "",
      password: "",
      confirmPassword: "",
    };
  },
  methods: {
    async registerUser() {
      if (this.password !== this.confirmPassword) {
        alert("Passwords do not match");
        return;
      }
      try {
        const response = await fetch("http://localhost:8000/api/v1/users", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            first_name: this.firstName,
            last_name: this.lastName,
            email: this.email,
            password: this.password,
          }),
        });
        if (!response.ok) {
          throw new Error("Register failed");
        }
        console.log("Register successful");

        // Automatically log the user in
        await this.loginUser();
        
      } catch (error) {
        console.error("Error during register:", error);
      }
    },
    async loginUser() {
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

        // Store the token in localStorage
        localStorage.setItem("token", data.access_token);

        console.log("Login successful");

        // Redirect to settings page
        this.$router.push('/settings');
      } catch (error) {
        console.error("Error during login:", error);
      }
    },
  },
});
</script>

<style scoped>
.register-form {
  padding-top: 40px;
  max-width: 350px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center; 
}

.form-group {
  margin-bottom: 20px;
}

ion-label {
  font-weight: bold;
}

ion-input {
  border-radius: 5px;
}

ion-button:hover {
  --background: #0056b3;
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

.custom_button {
  --background: #75f4c7;
  width: 300px;
  color: #000000;
  font-weight: bold;
}

</style>
