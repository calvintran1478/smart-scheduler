<template>
    <ion-modal :is-open="true" @didDismiss="closeModal">
      <ion-header>
        <ion-toolbar>
          <ion-title>Add Habit</ion-title>
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
          <ion-label position="stacked">Repeat Interval</ion-label>
          <ion-select v-model="repeat_interval" placeholder="Select repeat interval">
            <ion-select-option value="Daily">Daily</ion-select-option>
            <ion-select-option value="Weekly">Weekly</ion-select-option>
            <ion-select-option value="Monthly">Monthly</ion-select-option>
            <ion-select-option value="Yearly">Yearly</ion-select-option>
          </ion-select>
        </ion-item>
        <ion-button expand="block" @click="createHabit">Create Habit</ion-button>
      </ion-content>
    </ion-modal>
  </template>
  
  <script>
  import { IonModal, IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonContent, IonItem, IonLabel, IonInput, IonSelect, IonSelectOption } from "@ionic/vue";
  import { defineComponent } from "vue";
  
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
    data() {
      return {
        name: '',
        frequency: 1,
        repeat_interval: 'Daily'
      };
    },
    methods: {
      closeModal() {
        this.$emit('close');
      },
      async createHabit() {
        const habit = {
          name: this.name,
          frequency: this.frequency,
          repeat_interval: this.repeat_interval
        };
  
        try {
          const response = await fetch('http://localhost:8000/api/v1/users/habits', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(habit)
          });
  
          if (response.status === 201) {
            const newHabit = await response.json();
            this.$emit('habit-created', newHabit);
            this.closeModal();
          } else {
            console.error('Failed to create habit:', response.statusText);
          }
        } catch (error) {
          console.error('Error creating habit:', error);
        }
      }
    }
  });
  </script>
  
  <style scoped>
  /* Add styling later */
  </style>
  