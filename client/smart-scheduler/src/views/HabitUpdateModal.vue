<template>
    <ion-modal :is-open="true" @didDismiss="closeModal">
      <ion-header>
        <ion-toolbar>
          <ion-title>Edit Habit</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeModal">Close</ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      <ion-content class="ion-padding">
        <ion-item>
          <ion-label position="stacked">Habit Name</ion-label>
          <ion-input v-model="name" placeholder="Enter habit name"></ion-input>
        </ion-item>
        <ion-item>
          <ion-label position="stacked">Frequency</ion-label>
          <ion-input v-model.number="frequency" type="number" min="1" placeholder="Enter frequency"></ion-input>
        </ion-item>
        <ion-item>
          <ion-label position="stacked">Duration (in minutes)</ion-label>
          <ion-input v-model.number="duration" type="number" min="1" aria-placeholder="Enter duration"></ion-input>
        </ion-item>
        <ion-item>
          <ion-label position="stacked">Repeat Interval</ion-label>
          <ion-select v-model="repeat_interval" placeholder="Select repeat interval">
            <ion-select-option value="Daily">Daily</ion-select-option>
            <ion-select-option value="Weekly">Weekly</ion-select-option>
            <ion-select-option value="Monthly">Monthly</ion-select-option>
            <ion-select-option value="Yearly">Yearly</ion-select-option>
          </ion-select>
        </ion-item>
        <ion-item>
          <ion-label position="stacked">Time Preference</ion-label>
          <ion-select v-model="time_preference" multiple placeholder="Select time preferences">
            <ion-select-option value="morning">Morning</ion-select-option>
            <ion-select-option value="afternoon">Afternoon</ion-select-option>
            <ion-select-option value="evening">Evening</ion-select-option>
            <ion-select-option value="night">Night</ion-select-option>
          </ion-select>
        </ion-item>
        <ion-button expand="block" @click="updateHabit">Update Habit</ion-button>
      </ion-content>
    </ion-modal>
  </template>
  
  <script>
  import { IonModal, IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonContent, IonItem, IonLabel, IonInput, IonSelect, IonSelectOption } from "@ionic/vue";
  import { defineComponent } from "vue";
  import { refreshToken, logout } from "../services/auth";
  
  export default defineComponent({
    components: {
      IonModal,
      IonHeader,
      IonToolbar,
      IonTitle,
      IonButtons,
      IonButton,
      IonContent,
      IonItem,
      IonLabel,
      IonInput,
      IonSelect,
      IonSelectOption
    },
    props: {
      habit: {
        type: Object,
        default: () => ({
          name: '',
          frequency: 1,
          duration: 1,
          repeat_interval: 'Daily',
          time_preference: []
        })
      }
    },
    data() {
      return {
        name: this.habit.name,
        frequency: this.habit.frequency,
        duration: this.habit.duration,
        repeat_interval: this.habit.repeat_interval,
        time_preference: this.habit.time_preference,
        refreshed: false,
      };
    },
    methods: {
      closeModal() {
        this.$emit('close');
      },
      async updateHabit() {
        const updatedHabit = {
          name: this.name,
          frequency: this.frequency,
          duration: this.duration,
          repeat_interval: this.repeat_interval,
          time_preference: this.time_preference
        };
  
        const token = localStorage.getItem("token");
        if (!token) {
          console.error("No token found");
          return;
        }
  
        try {
          const response = await fetch(`http://localhost:8000/api/v1/users/habits/${this.habit.name}`, {
            method: 'PATCH',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: "include",
            body: JSON.stringify(updatedHabit)
          });
  
          if (response.status === 204) {
            this.$emit('habit-updated');
            this.closeModal();
            console.log('Update habit successful');
          } else if (response.status == 401) {
            // refresh token
            if (!this.refreshed) {
              await refreshToken();
              this.refreshed = true;
              console.log('Token refresh successful.')
              // try again
              this.updateHabit()
            } else {
              console.log('Time out.')
              logout();
            }
          } else {
            console.error('Failed to update habit:', response.statusText);
          }
        } catch (error) {
          console.error('Error updating habit:', error);
        }
      }
    }
  });
  </script>
  
  <style scoped>
  /* Add styling later */
  </style>
  