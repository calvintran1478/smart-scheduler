<template>
    <ion-page>
      <ion-content class="ion-padding">
        <h1 class="title">Build good habits</h1>
        <ion-list>
          <ion-item v-for="habit in habits" :key="habit.name">
            <ion-label>
              <h2>{{ habit.name }}</h2>
              <p>{{ habit.frequency }} times {{ habit.repeat_interval.toLowerCase() }}</p>
            </ion-label>
            <ion-button slot="end" @click="editHabit(habit)">Edit</ion-button>
          </ion-item>
        </ion-list>
        <ion-fab vertical="bottom" horizontal="end" slot="fixed">
          <ion-fab-button @click="openModal">
            <ion-icon :icon="addOutline"></ion-icon>
          </ion-fab-button>
        </ion-fab>
        <habit-modal v-if="isModalOpen" @close="closeModal" @habit-created="addHabit" />
        <habit-edit-modal
          v-if="isEditModalOpen"
          :habit="selectedHabit"
          @close="closeEditModal"
          @habit-updated="updateHabit"
      />
      </ion-content>
    </ion-page>
  </template>
  
  <script>
  import { IonPage, IonContent, IonList, IonItem, IonLabel, IonFab, IonFabButton, IonIcon } from "@ionic/vue";
  import { addOutline } from "ionicons/icons";
  import HabitModal from './HabitModal.vue';
  import { defineComponent } from "vue";
  import HabitEditModal from './HabitUpdateModal.vue';
  
  export default defineComponent({
    components: {
      IonPage,
      IonContent,
      IonList,
      IonItem,
      IonLabel,
      IonFab,
      IonFabButton,
      IonIcon,
      HabitModal,
      HabitEditModal
    },
    data() {
      return {
        habits: [],
        isModalOpen: false,
        addOutline: addOutline,
        isEditModalOpen: false,
        selectedHabit: null,
      };
    },
    methods: {
      async fetchHabits() {
        const token = localStorage.getItem("token");
        if (!token) {
            console.error("No token found");
            return;
        }
        try {
          const response = await fetch('http://localhost:8000/api/v1/users/habits', {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: "include"
          });

          if (response.status === 200) {
            const data = await response.json();
            this.habits = data.habits;
            console.log("Fetch habits successful.");
          } else {
            console.error('Failed to fetch habits:', response.statusText);
          }
        } catch (error) {
          console.error('Error fetching habits:', error);
        }
      },
      openModal() {
        this.isModalOpen = true;
      },
      closeModal() {
        this.isModalOpen = false;
      },
      addHabit(newHabit) {
        this.habits.push(newHabit);
      },
      async editHabit(habit) {
        await this.fetchHabits();
        this.isEditModalOpen = true;
        this.selectedHabit = habit;
      },
      closeEditModal() {
        this.isEditModalOpen = false;
      }
    },
    mounted() {
      this.fetchHabits();
    }
  });
  </script>
  
  <style scoped>
  .title {
    padding-top: 30px;
    font-size: 28px;
    font-weight: bold;
    text-align: left;
    padding-left: 25px;
  }
  </style>
  